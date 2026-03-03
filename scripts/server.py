#!/usr/bin/env python3
"""
Open Booth — Chunk Upload Server
Receives chunks from recorder.html and serves session state to monitor.html.

Usage:
    python3 server.py [--port 8080] [--chunks-dir ./chunks]

Deploy to your VPS:
    1. Copy this file to your VPS
    2. Run: python3 server.py --port 8080
    3. Use a reverse proxy (nginx/caddy) to expose it over HTTPS
    4. Set UPLOAD_ENDPOINT = 'https://your-domain.com/upload' in recorder.html
    5. Set SESSION_STATE_URL = 'https://your-domain.com/session-state' in monitor.html

Nginx config snippet:
    location /upload        { proxy_pass http://localhost:8080; }
    location /session-state { proxy_pass http://localhost:8080; }

Requirements:
    Python 3.9+ (no external dependencies)
"""

import http.server
import json
import os
import sys
import time
import argparse
import cgi
import io
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from collections import defaultdict


# ─── CONFIG ───────────────────────────────────────────────────────────────────
DEFAULT_PORT       = 8080
MAX_CHUNK_MB       = 200   # reject chunks larger than this
ALLOWED_EXTENSIONS = {'.mp4', '.webm'}
# ─────────────────────────────────────────────────────────────────────────────


class SessionState:
    """In-memory session state. Rebuilt from disk on restart."""

    def __init__(self):
        self._sessions = defaultdict(lambda: {
            'startedAt': None,
            'participants': {}
        })

    def record_chunk(self, session: str, participant: str, index: int, size: int, filename: str):
        s = self._sessions[session]
        if not s['startedAt']:
            s['startedAt'] = int(time.time() * 1000)

        p = s['participants'].setdefault(participant, {
            'lastChunkAt':    0,
            'chunksUploaded': 0,
            'totalBytes':     0,
            'duration':       0,
            'errors':         0
        })

        p['lastChunkAt']     = int(time.time() * 1000)
        p['chunksUploaded'] += 1
        p['totalBytes']     += size
        # Rough duration estimate: each server chunk ~= 10s
        p['duration'] = p['chunksUploaded'] * 10

        return True

    def record_error(self, session: str, participant: str):
        try:
            self._sessions[session]['participants'][participant]['errors'] += 1
        except Exception:
            pass

    def get_session(self, session: str) -> dict:
        s = self._sessions.get(session)
        if not s:
            return {'session': session, 'startedAt': None, 'participants': {}}
        return {'session': session, **s}

    def all_sessions(self) -> list:
        return list(self._sessions.keys())


state = SessionState()


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Custom log format
        ts = time.strftime('%H:%M:%S')
        print(f"  [{ts}] {fmt % args}")

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/session-state':
            self.handle_session_state(parsed)
        elif parsed.path == '/health':
            self.handle_health()
        elif parsed.path == '/sessions':
            self.handle_sessions_list()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == '/upload':
            self.handle_upload()
        else:
            self.send_response(404)
            self.end_headers()

    # ── UPLOAD ──────────────────────────────────────────────────────────────
    def handle_upload(self):
        try:
            content_type  = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))

            if content_length > MAX_CHUNK_MB * 1024 * 1024:
                self.respond(413, {'error': 'Chunk too large'})
                return

            if 'multipart/form-data' not in content_type:
                self.respond(400, {'error': 'Expected multipart/form-data'})
                return

            # Parse multipart
            body = self.rfile.read(content_length)

            form = self.parse_multipart(content_type, body)

            session     = form.get('session', [''])[0]
            participant = form.get('participant', [''])[0]
            index_str   = form.get('index', ['0'])[0]
            filename    = form.get('filename', ['chunk.mp4'])[0]
            chunk_data  = form.get('chunk_data', [b''])[0]

            if not session or not participant:
                self.respond(400, {'error': 'Missing session or participant'})
                return

            # Sanitise filename
            safe_filename = sanitise_filename(filename)
            if not safe_filename:
                self.respond(400, {'error': 'Invalid filename'})
                return

            ext = Path(safe_filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                self.respond(400, {'error': f'Invalid file type: {ext}'})
                return

            # Save chunk
            session_dir = CHUNKS_DIR / sanitise_path(session)
            session_dir.mkdir(parents=True, exist_ok=True)
            chunk_path  = session_dir / safe_filename

            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)

            size = len(chunk_data)
            idx  = int(index_str) if index_str.isdigit() else 0

            state.record_chunk(session, participant, idx, size, safe_filename)

            print(f"  ↑ {participant} / {safe_filename} ({fmt_size(size)})")

            self.respond(200, {
                'ok':          True,
                'session':     session,
                'participant': participant,
                'index':       idx,
                'size':        size,
                'filename':    safe_filename
            })

        except Exception as e:
            print(f"  ✗ Upload error: {e}")
            self.respond(500, {'error': str(e)})

    def parse_multipart(self, content_type: str, body: bytes) -> dict:
        """Parse multipart/form-data. Returns dict of field -> [value(s)]."""
        # Extract boundary
        boundary = None
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                boundary = part[9:].strip('"')
                break

        if not boundary:
            return {}

        result = defaultdict(list)
        boundary_bytes = ('--' + boundary).encode()

        parts = body.split(boundary_bytes)

        for part in parts[1:]:  # skip preamble
            if part.strip() in (b'', b'--', b'--\r\n'):
                continue
            # Split headers from body
            if b'\r\n\r\n' in part:
                headers_raw, content = part.split(b'\r\n\r\n', 1)
            elif b'\n\n' in part:
                headers_raw, content = part.split(b'\n\n', 1)
            else:
                continue

            # Strip trailing boundary marker
            if content.endswith(b'\r\n'):
                content = content[:-2]

            headers_str = headers_raw.decode('utf-8', errors='replace')

            # Extract field name and filename
            field_name = None
            is_file    = False
            for line in headers_str.split('\r\n'):
                if 'Content-Disposition' in line:
                    for item in line.split(';'):
                        item = item.strip()
                        if item.startswith('name='):
                            field_name = item[5:].strip('"')
                        if item.startswith('filename='):
                            is_file = True

            if field_name is None:
                continue

            if is_file or field_name == 'chunk':
                result['chunk_data'].append(content)
            else:
                result[field_name].append(content.decode('utf-8', errors='replace'))

        return dict(result)

    # ── SESSION STATE ────────────────────────────────────────────────────────
    def handle_session_state(self, parsed):
        qs      = parse_qs(parsed.query)
        session = qs.get('session', [None])[0]

        if not session:
            self.respond(400, {'error': 'Missing session parameter'})
            return

        data = state.get_session(session)
        self.respond(200, data)

    # ── HEALTH ───────────────────────────────────────────────────────────────
    def handle_health(self):
        self.respond(200, {
            'ok':       True,
            'sessions': len(state.all_sessions()),
            'time':     int(time.time())
        })

    # ── SESSIONS LIST ────────────────────────────────────────────────────────
    def handle_sessions_list(self):
        sessions = state.all_sessions()
        self.respond(200, {'sessions': sessions})

    # ── HELPERS ──────────────────────────────────────────────────────────────
    def respond(self, code: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type',   'application/json')
        self.send_header('Content-Length', len(body))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


# ─── UTILS ────────────────────────────────────────────────────────────────────
def sanitise_filename(name: str) -> str:
    """Allow only safe characters in filenames."""
    name = os.path.basename(name)
    safe = re.sub(r'[^\w\-.]', '_', name) if name else ''
    return safe if safe else ''

def sanitise_path(name: str) -> str:
    """Allow only safe characters in directory names."""
    import re
    return re.sub(r'[^\w\-]', '_', name)

def fmt_size(b: int) -> str:
    if b < 1024: return f"{b}B"
    if b < 1048576: return f"{b/1024:.0f}KB"
    return f"{b/1048576:.1f}MB"

import re  # need at module level


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    global CHUNKS_DIR

    parser = argparse.ArgumentParser(description='Open Booth chunk upload server')
    parser.add_argument('--port',       type=int, default=int(os.environ.get('OB_PORT', DEFAULT_PORT)),   help=f'Port (default: {DEFAULT_PORT})')
    parser.add_argument('--chunks-dir', default=os.environ.get('OB_CHUNKS_DIR', './chunks'),              help='Where to save chunks (default: ./chunks)')
    args = parser.parse_args()

    global MAX_CHUNK_MB
    MAX_CHUNK_MB = int(os.environ.get('OB_MAX_CHUNK_MB', MAX_CHUNK_MB))

    CHUNKS_DIR = Path(args.chunks_dir)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n  Open Booth — Chunk Server")
    print(f"  {'─' * 40}")
    print(f"  Port:       {args.port}")
    print(f"  Chunks dir: {CHUNKS_DIR.resolve()}")
    print(f"  Endpoints:")
    print(f"    POST /upload          Receive chunks from recorder")
    print(f"    GET  /session-state   Session data for monitor")
    print(f"    GET  /health          Health check")
    print(f"  {'─' * 40}\n")

    server = http.server.HTTPServer(('0.0.0.0', args.port), Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  Server stopped.")


if __name__ == '__main__':
    main()