# Open Booth Architecture

**Purpose:** Visual and structural reference for how Open Booth works
**Status:** Living document
**Created:** 2026-03-17
**Version:** 1.0.0

---

## The Big Picture

Open Booth is a browser-based podcast recording tool — free, open source, self-hosted on a $6/month droplet. Each participant records their own microphone independently with dual-encoder redundancy. It is NOT a WebRTC tool and does not capture remote audio.

```
┌─────────────────────────────────────────────────────────────┐
│                       OPEN BOOTH                              │
│                                                              │
│  "Reliable local recording — a URL is enough"                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Each participant opens a URL in Chrome               │   │
│  │                                                       │   │
│  │  Two encoders run simultaneously:                     │   │
│  │                                                       │   │
│  │  Encoder A (server)  ── 800 kbps ── 10s chunks ──►   │   │
│  │                                     upload to VPS     │   │
│  │                                                       │   │
│  │  Encoder B (local)   ── 4000 kbps ─ 30s chunks ──►   │   │
│  │                                     IndexedDB cache   │   │
│  │                                                       │   │
│  │  If network drops → local cache covers the gap        │   │
│  │  If browser crashes → server chunks recover           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Post-session: assemble.py merges chunks per participant     │
│  → prefers local (higher quality) over server                │
│  → detects gaps, generates report                            │
│  → outputs final MP4 per participant                         │
│                                                              │
│  Open source · MIT license · $6/month hosting                │
└─────────────────────────────────────────────────────────────┘
```

---

## Recording Flow

Dual encoders ensure no data loss even if the network fails.

```
    Participant opens recorder.html
         │
         ▼
    ┌──────────────────────────────────────────────────┐
    │  Browser (Chrome)                                 │
    │                                                   │
    │  getUserMedia() → microphone stream               │
    │                                                   │
    │  ┌─────────────────┐  ┌─────────────────┐       │
    │  │ Encoder A        │  │ Encoder B        │       │
    │  │ (server stream)  │  │ (local cache)    │       │
    │  │                  │  │                  │       │
    │  │ 800 kbps         │  │ 4000 kbps        │       │
    │  │ 10s chunks       │  │ 30s chunks       │       │
    │  │                  │  │                  │       │
    │  │ → HTTP upload    │  │ → IndexedDB      │       │
    │  │   (3 retries)    │  │   (survives      │       │
    │  │                  │  │    restart)       │       │
    │  └────────┬─────────┘  └────────┬─────────┘       │
    │           │                     │                  │
    │           │  + "Rescue Download"│                  │
    │           │    (manual fallback)│                  │
    └───────────┼─────────────────────┼──────────────────┘
                │                     │
                ▼                     ▼
    ┌──────────────┐          ┌──────────────┐
    │  VPS disk    │          │  Browser DB  │
    │  /chunks/    │          │  (IndexedDB) │
    │  {session}/  │          │              │
    └──────────────┘          └──────────────┘
```

---

## Assembly — Post-Session

Host runs `assemble.py` on their Mac. Discovers chunks, deduplicates, fills gaps, outputs clean MP4.

```
    ┌──────────────────────────────────────────────────┐
    │  assemble.py                                      │
    │                                                   │
    │  1. Discover all chunks for session               │
    │     (server + local + rescue)                     │
    │                                                   │
    │  2. Deduplicate                                   │
    │     Prefer local (4000 kbps) over                 │
    │     server (800 kbps) when both exist             │
    │                                                   │
    │  3. Detect gaps                                   │
    │     Report missing chunk indices                  │
    │     with approximate duration                     │
    │                                                   │
    │  4. Assemble per participant                      │
    │     ffmpeg: fragmented MP4 → clean MP4            │
    │                                                   │
    │  5. Output                                        │
    │     {participant}_final.mp4                        │
    │     assembly_report.txt                           │
    └──────────────────────────────────────────────────┘
```

---

## Host Coordination

One participant is the host. They control start/stop for all guests via HTTP polling.

```
    HOST (recorder.html?role=host)
         │
         ├── "Start All" → POST /session-command
         ├── "Stop All"  → POST /session-command
         └── "Chapter"   → POST /session-command (with label)
                │
                ▼
    ┌──────────────────────┐
    │  server.py            │
    │  (in-memory state)    │
    │                       │
    │  Commands queue:      │
    │  [{type, timestamp,   │
    │    label}]            │
    └──────────┬───────────┘
               │
               ▼
    GUESTS poll every 2s:
    GET /session-commands
         │
         ▼
    Auto-start/stop recording
    (manual fallback always available)
```

---

## Monitor Dashboard

Read-only live view for the host showing session health.

```
    monitor.html
    ┌──────────────────────────────────────┐
    │  Session: PB-20260317-A1B2           │
    │  Started: 14:23:05                   │
    │                                      │
    │  Jason (host)                        │
    │  ████████████░░░░  12 chunks, 45 MB  │
    │                                      │
    │  Gav (guest)                          │
    │  ██████████░░░░░░  10 chunks, 38 MB  │
    │                                      │
    │  Chapters:                           │
    │  • 00:05:23 — Intro                  │
    │  • 00:15:47 — Main topic             │
    │                                      │
    │  Activity log:                       │
    │  14:23:12 Jason: chunk 1 uploaded    │
    │  14:23:14 Gav: chunk 1 uploaded      │
    │  ...                                 │
    └──────────────────────────────────────┘

    Polls /session-state every 5s
```

---

## Architecture

Three components, zero external dependencies on the server.

```
    ┌─────────────────────────────────────────────────────┐
    │  Browser                                             │
    │                                                      │
    │  recorder.html (936 lines)                           │
    │  • Dual MediaRecorder instances                      │
    │  • IndexedDB chunk caching                           │
    │  • HTTP upload with retry                            │
    │  • Host command polling                              │
    │                                                      │
    │  monitor.html                                        │
    │  • Live session dashboard                            │
    │  • Read-only                                         │
    └────────────────────────┬─────────────────────────────┘
                             │ HTTPS
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │  Nginx (port 80/443)                                 │
    │  / → static HTML                                     │
    │  /upload, /register, /session-* → :8080              │
    └────────────────────────┬─────────────────────────────┘
                             │
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │  server.py (517 lines, Python stdlib only)           │
    │                                                      │
    │  POST /upload        ── receive chunks               │
    │  POST /register      ── participant joins            │
    │  POST /session-command ── host sends start/stop      │
    │  GET  /session-commands ── guests poll               │
    │  GET  /session-state ── monitor fetches metrics      │
    │  GET  /health        ── health check                 │
    │                                                      │
    │  Zero external dependencies                          │
    │  In-memory session state (rebuilt from disk)          │
    │  Chunks stored: /opt/openbooth/chunks/{session}/     │
    └─────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────┐
    │  assemble.py (395 lines, runs on host's Mac)         │
    │  Requires: ffmpeg                                    │
    └─────────────────────────────────────────────────────┘
```

---

## Deployment

30-minute setup on a $6/month DigitalOcean droplet.

```
    ┌─────────────────────────────────────────┐
    │  DigitalOcean Droplet                    │
    │  1GB RAM · 1 CPU · $6/month              │
    │  Ubuntu 24.04 LTS                        │
    │                                          │
    │  /var/www/openbooth/                     │
    │  └── client/ (HTML, JS, CSS)             │
    │                                          │
    │  /opt/openbooth/                         │
    │  ├── server.py (systemd service)         │
    │  └── chunks/{session_id}/                │
    │                                          │
    │  Nginx → :8080 (server.py)               │
    │  Optional: Let's Encrypt HTTPS           │
    └─────────────────────────────────────────┘

    Also works locally:
    Open recorder.html directly in Chrome
    → records to IndexedDB only (no server needed)
```

---

## Source Files

| File | Purpose | Lines |
|------|---------|-------|
| `client/recorder.html` | Recording UI + dual encoder | ~936 |
| `client/monitor.html` | Live session dashboard | ~200 |
| `client/config.example.js` | Configuration template | ~30 |
| `scripts/server.py` | HTTP server (zero deps) | ~517 |
| `scripts/assemble.py` | Chunk assembly + dedup | ~395 |
| `docs/VPS_SETUP.md` | 30-minute deploy guide | ~150 |

---

**End Architecture Document**
