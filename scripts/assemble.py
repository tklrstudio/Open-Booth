#!/usr/bin/env python3
"""
Open Booth — Chunk Assembler
Merges server chunks + local rescue chunks per participant,
deduplicates, detects gaps, and outputs clean MP4s.

Usage:
    python3 assemble.py <session_id> [options]

Options:
    --chunks-dir DIR     Directory containing chunks (default: ./chunks)
    --output-dir DIR     Output directory (default: ./sessions)
    --participants LIST   Comma-separated participant IDs to assemble
                         (default: auto-detect from files)

Examples:
    # Auto-detect all participants
    python3 assemble.py OB-20260306-A3BX

    # Specific participants, custom dirs
    python3 assemble.py OB-20260306-A3BX --participants Alice-4F2X,Bob-9KL3

    # Custom directories
    python3 assemble.py OB-20260306-A3BX --chunks-dir ~/Downloads --output-dir ~/Podcasts

Output per participant:
    sessions/OB-20260306-A3BX/
        Alice-4F2X_final.mp4       ← best available quality
        Bob-9KL3_final.mp4
        assembly_report.txt        ← what was used, any gaps

Requirements:
    - Python 3.9+
    - ffmpeg: brew install ffmpeg
"""

import argparse
import os
import re
import subprocess
import sys
import glob
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# ─── COLOURS ─────────────────────────────────────────────────────────────────
class C:
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    CYAN   = '\033[96m'
    DIM    = '\033[90m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

def ok(msg):   print(f"{C.GREEN}  ✓ {msg}{C.RESET}")
def warn(msg): print(f"{C.YELLOW}  ⚠ {msg}{C.RESET}")
def err(msg):  print(f"{C.RED}  ✗ {msg}{C.RESET}")
def info(msg): print(f"{C.DIM}    {msg}{C.RESET}")
def hdr(msg):  print(f"\n{C.BOLD}{C.CYAN}{msg}{C.RESET}")


# ─── CHUNK DISCOVERY ─────────────────────────────────────────────────────────
class Chunk:
    """Represents one recorded chunk file."""
    def __init__(self, path: Path, session: str, participant: str, layer: str, index: int):
        self.path        = path
        self.session     = session
        self.participant = participant
        self.layer       = layer   # 'srv' or 'local'
        self.index       = index
        self.size        = path.stat().st_size if path.exists() else 0

    def __repr__(self):
        return f"Chunk({self.participant}/{self.layer}/{self.index}, {fmt_size(self.size)})"


def discover_chunks(chunks_dir: Path, session_id: str) -> dict[str, list[Chunk]]:
    """
    Find all chunks for a session, grouped by participant.
    Filename pattern: {session}_{participant}_{layer}_{index}.{ext}
    Layer is either 'srv' (server) or 'local' (IndexedDB rescue download).
    """
    pattern = re.compile(
        r'^(?P<session>[^_]+(?:_[^_]+)*?)_(?P<participant>[^_]+(?:-[A-Z0-9]+)?)_(?P<layer>srv|local|server)_(?P<index>\d+)\.(?P<ext>mp4|webm)$'
    )

    by_participant = defaultdict(list)

    for ext in ['*.mp4', '*.webm']:
        for fpath in chunks_dir.glob(ext):
            m = pattern.match(fpath.name)
            if not m:
                continue
            if m.group('session') != session_id:
                continue

            layer = m.group('layer')
            if layer == 'server': layer = 'srv'

            chunk = Chunk(
                path        = fpath,
                session     = m.group('session'),
                participant = m.group('participant'),
                layer       = layer,
                index       = int(m.group('index')),
            )
            by_participant[chunk.participant].append(chunk)

    return dict(by_participant)


def auto_detect_participants(chunks_dir: Path, session_id: str) -> list[str]:
    """Return list of participant IDs found in chunks dir for this session."""
    chunks = discover_chunks(chunks_dir, session_id)
    return sorted(chunks.keys())


# ─── DEDUPLICATION + MERGE STRATEGY ─────────────────────────────────────────
def build_chunk_sequence(all_chunks: list[Chunk]) -> tuple[list[Chunk], list[dict]]:
    """
    Given all chunks for a participant (srv + local, possibly overlapping),
    build the best possible ordered sequence.

    Strategy:
    - Group by index
    - For each index, prefer 'local' (higher quality) over 'srv'
    - Report any gaps in the index sequence
    - Return ordered chunk list + report of decisions
    """
    by_index = defaultdict(list)
    for c in all_chunks:
        by_index[c.index].append(c)

    if not by_index:
        return [], []

    indices = sorted(by_index.keys())
    sequence = []
    report   = []

    for idx in indices:
        candidates = by_index[idx]
        # Prefer local (higher quality), then srv
        local_cands = [c for c in candidates if c.layer == 'local']
        srv_cands   = [c for c in candidates if c.layer == 'srv']

        if local_cands:
            chosen = max(local_cands, key=lambda c: c.size)  # largest = most complete
            source = 'local cache (full quality)'
            if srv_cands:
                report.append({'index': idx, 'action': 'dedup', 'msg': f'Index {idx}: used local, discarded {len(srv_cands)} server copy(s)'})
        elif srv_cands:
            chosen = max(srv_cands, key=lambda c: c.size)
            source = 'server (degraded quality)'
        else:
            continue

        sequence.append(chosen)
        report.append({'index': idx, 'action': 'use', 'msg': f'Index {idx}: {chosen.path.name} [{source}, {fmt_size(chosen.size)}]'})

    # Detect gaps
    gaps = []
    for i in range(len(indices) - 1):
        if indices[i+1] - indices[i] > 1:
            missing = list(range(indices[i]+1, indices[i+1]))
            gaps.append(missing)
            report.append({'index': indices[i], 'action': 'gap', 'msg': f'⚠ GAP detected: indices {missing} missing ({len(missing) * 10}s of audio/video)'})

    return sequence, report, gaps


# ─── ASSEMBLY ────────────────────────────────────────────────────────────────
def write_concat_list(chunks: list[Chunk], list_file: Path):
    with open(list_file, 'w') as f:
        for c in chunks:
            escaped = str(c.path.resolve()).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")


def assemble_participant(participant: str, all_chunks: list[Chunk], output_dir: Path, session_id: str) -> dict:
    hdr(f"  {participant}")

    srv_chunks   = [c for c in all_chunks if c.layer == 'srv']
    local_chunks = [c for c in all_chunks if c.layer == 'local']
    info(f"Found {len(srv_chunks)} server chunks, {len(local_chunks)} local cache chunks")

    sequence, report, gaps = build_chunk_sequence(all_chunks)

    if not sequence:
        err("No usable chunks found — skipping")
        return {'participant': participant, 'success': False, 'error': 'no chunks'}

    # Note: chunk 0 is the init segment prepended into all subsequent chunks by the recorder.
    # All chunks are self-contained — no filtering needed.

    # Print report
    for r in report:
        if r['action'] == 'gap':    warn(r['msg'])
        elif r['action'] == 'dedup': info(r['msg'])

    output_file = output_dir / f"{participant}_final.mp4"
    list_file   = output_dir / f"{participant}_concat.txt"

    # Browser MediaRecorder produces fragmented MP4s that ffmpeg can't concat directly.
    # Strategy: re-encode each chunk to a clean MP4 individually, then concat those.
    info(f"Assembling {len(sequence)} chunks → {output_file.name}")
    temp_dir = output_dir / f"{participant}_temp"
    temp_dir.mkdir(exist_ok=True)
    converted = []

    for c in sequence:
        temp_out = temp_dir / f"chunk_{str(c.index).zfill(4)}.mp4"
        info(f"  Converting chunk {c.index} ({fmt_size(c.size)})...")
        r = subprocess.run([
            'ffmpeg', '-y',
            '-i', str(c.path),
            '-c:v', 'libx264', '-c:a', 'aac',
            '-crf', '17', '-preset', 'fast',
            str(temp_out)
        ], capture_output=True, text=True)
        if r.returncode != 0:
            err(f"  Chunk {c.index} failed:\n{r.stderr[-400:]}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {'participant': participant, 'success': False, 'error': f'chunk {c.index} conversion failed'}
        converted.append(temp_out)

    if len(converted) == 1:
        shutil.move(str(converted[0]), str(output_file))
        shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        with open(list_file, 'w') as f:
            for p in converted:
                f.write(f"file '{str(p.resolve())}'\n")
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', str(list_file),
            '-c', 'copy',
            str(output_file)
        ], capture_output=True, text=True)
        list_file.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        if result.returncode != 0:
            err(f"ffmpeg concat failed:\n{result.stderr[-800:]}")
            return {'participant': participant, 'success': False, 'error': 'ffmpeg concat error'}

    size_mb = output_file.stat().st_size / (1024 * 1024)
    ok(f"{output_file.name} — {size_mb:.1f} MB")

    return {
        'participant': participant,
        'success':     True,
        'output':      str(output_file),
        'chunks_used': len(sequence),
        'gaps':        gaps,
        'size_mb':     size_mb,
        'report':      report
    }


# ─── REPORT ──────────────────────────────────────────────────────────────────
def write_report(session_id: str, results: list[dict], output_dir: Path):
    report_file = output_dir / 'assembly_report.txt'
    lines = [
        f"Open Booth — Assembly Report",
        f"Session:   {session_id}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
    ]

    for r in results:
        lines.append(f"{'─' * 50}")
        lines.append(f"Participant: {r['participant']}")
        if r['success']:
            lines.append(f"Status:  OK")
            lines.append(f"Output:  {Path(r['output']).name}")
            lines.append(f"Chunks:  {r['chunks_used']}")
            lines.append(f"Size:    {r['size_mb']:.1f} MB")
            if r['gaps']:
                for gap in r['gaps']:
                    lines.append(f"⚠ GAP:  indices {gap} missing (~{len(gap)*10}s)")
            lines.append("")
            lines.append("Chunk decisions:")
            for entry in r.get('report', []):
                lines.append(f"  {entry['msg']}")
        else:
            lines.append(f"Status:  FAILED — {r.get('error','unknown')}")
        lines.append("")

    with open(report_file, 'w') as f:
        f.write('\n'.join(lines))

    ok(f"Assembly report → {report_file.name}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def check_ffmpeg():
    try:
        return subprocess.run(['ffmpeg', '-version'], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def fmt_size(b):
    if b < 1024: return f"{b}B"
    if b < 1048576: return f"{b/1024:.0f}KB"
    return f"{b/1048576:.1f}MB"


def main():
    parser = argparse.ArgumentParser(description='Open Booth chunk assembler')
    parser.add_argument('session_id',     help='Session ID (e.g. OB-20260306-A3BX)')
    parser.add_argument('--chunks-dir',   default='./chunks',   help='Directory containing chunks')
    parser.add_argument('--output-dir',   default='./sessions', help='Output root directory')
    parser.add_argument('--participants', default=None,          help='Comma-separated participant IDs (default: auto)')
    args = parser.parse_args()

    print(f"\n{C.BOLD}Open Booth — Chunk Assembler{C.RESET}")
    print(f"{'─' * 50}")

    if not check_ffmpeg():
        err("ffmpeg not found. Install: brew install ffmpeg")
        sys.exit(1)

    chunks_dir = Path(args.chunks_dir)
    if not chunks_dir.exists():
        err(f"Chunks directory not found: {chunks_dir}")
        sys.exit(1)

    # Discover
    all_chunks = discover_chunks(chunks_dir, args.session_id)

    if not all_chunks:
        err(f"No chunks found for session {args.session_id} in {chunks_dir}")
        sys.exit(1)

    # Participants
    if args.participants:
        participant_ids = [p.strip() for p in args.participants.split(',')]
    else:
        participant_ids = sorted(all_chunks.keys())

    print(f"Session:      {args.session_id}")
    print(f"Chunks dir:   {chunks_dir.resolve()}")
    print(f"Participants: {', '.join(participant_ids)}")

    # Output dir
    output_dir = Path(args.output_dir) / args.session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output:       {output_dir.resolve()}")

    # Assemble each participant
    results = []
    for pid in participant_ids:
        if pid not in all_chunks:
            warn(f"No chunks found for participant: {pid}")
            results.append({'participant': pid, 'success': False, 'error': 'no chunks found'})
            continue
        result = assemble_participant(pid, all_chunks[pid], output_dir, args.session_id)
        results.append(result)

    # Write report
    hdr("  Assembly Report")
    write_report(args.session_id, results, output_dir)

    # Final summary
    hdr("  Summary")
    success = [r for r in results if r['success']]
    failed  = [r for r in results if not r['success']]
    any_gaps = any(r.get('gaps') for r in success)

    if success:
        ok(f"{len(success)} participant(s) assembled successfully")
        print(f"\n  Output files:")
        for r in success:
            gap_note = f" {C.YELLOW}[{sum(len(g) for g in r['gaps'])} gap(s)]{C.RESET}" if r['gaps'] else ''
            print(f"    {C.CYAN}{Path(r['output']).name}{C.RESET} — {r['size_mb']:.1f} MB{gap_note}")

    if failed:
        err(f"{len(failed)} participant(s) failed: {', '.join(r['participant'] for r in failed)}")

    if any_gaps:
        warn("Gaps detected in one or more participants — check assembly_report.txt")
        warn("Gaps indicate dropped chunks. The local rescue download may have them.")

    print()
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()