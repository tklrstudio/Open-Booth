# Open Booth

Browser-based podcast recording with triple redundancy. No software installs for participants.

---

## How it works

Each participant opens a URL in Chrome. Two encoders run simultaneously — a degraded stream uploads to the server in 10-second chunks, while a full-quality stream saves to the browser's local cache every 30 seconds. If the internet drops, the local cache covers the gap. After the session, the assembler merges both sources, deduplicates, and outputs clean MP4s ready for editing.

```
Recording
├── Encoder A (800kbps) → 10s chunks → Server (primary delivery)
└── Encoder B (4000kbps) → 30s chunks → IndexedDB (local cache)
                                       └── Rescue download (manual fallback)

Assembly
├── Server chunks (most recent / most complete set)
├── Local rescue chunks (fill any gaps from network drops)
└── Deduplication → participant_final.mp4
```

---

## Files

| File | Purpose |
|------|---------|
| `client/recorder.html` | Recording page — each participant opens this |
| `client/monitor.html`  | Live session dashboard — open this during recording |
| `client/config.example.js` | Configuration template — copy to `config.js` |
| `scripts/server.py`     | Chunk upload receiver + session state server |
| `scripts/assemble.py`   | Post-session chunk assembly |
| `docs/VPS_SETUP.md`     | Full step-by-step server setup guide |
| `.env.example`           | Server environment variable template |

---

## Infrastructure

Everything runs on a single DigitalOcean droplet ($6/month, Sydney region).

```
Droplet (YOUR_IP)
├── Nginx (port 80) — public facing
│   ├── /recorder.html  → serves recorder page
│   ├── /monitor.html   → serves monitor page
│   ├── /upload         → proxies to chunk server
│   └── /session-state  → proxies to chunk server
└── server.py (port 8080) — internal only
    └── /opt/openbooth/chunks/
```

See `VPS_SETUP.md` for the complete setup walkthrough.

---

## Setup

### Phase 1 — Test locally (no server needed)

Open `client/recorder.html` directly in Chrome. Without a config file, the page falls back to IndexedDB only. After recording, click **Download Local Cache (Rescue)** to get your chunks.

Use this to validate recording quality before touching the server.

### Phase 2 — Configure

```bash
cd client
cp config.example.js config.js
```

Edit `config.js` with your server's URL:

```javascript
const OB_CONFIG = {
  UPLOAD_ENDPOINT:   'https://your-domain.com/upload',
  SESSION_STATE_URL: 'https://your-domain.com/session-state',
};
```

`config.js` is gitignored — your settings won't be committed.

### Phase 3 — Deploy to server

Follow `docs/VPS_SETUP.md` end to end. Upload the HTML files and your `config.js` to the server.

---

## Running a session

### Before the session

The recorder generates a session ID automatically on first load — it appears in the address bar and in the top-right of the page. Copy the full URL and send it to your co-host.

```
# Both participants use the same URL
http://YOUR_IP/recorder.html?session=OB-20260306-A3BX

# Open the monitor in a separate tab
http://YOUR_IP/monitor.html?session=OB-20260306-A3BX
```

### During the session

1. Both participants open the recorder URL in Chrome
2. Enter name when prompted — unique suffix added automatically (e.g. `Alice → Alice-9KL3`)
3. Allow camera and microphone
4. Click **Start Recording**
5. Do your clap sync: "3, 2, 1, clap"
6. Your call software runs in a separate tab as normal
7. Watch the monitor in another tab
8. Click **Stop** when done

### After the session

```bash
# Download chunks from server to your Mac
scp -r root@YOUR_IP:/opt/openbooth/chunks/OB-20260306-A3BX ~/Podcasts/chunks/

# If a participant had a network dropout, ask them to click Rescue Download
# They send you the downloaded files → add them to the same chunks folder

# Assemble (requires ffmpeg: brew install ffmpeg)
python3 assemble.py OB-20260306-A3BX --chunks-dir ~/Podcasts/chunks/OB-20260306-A3BX

# Output
sessions/OB-20260306-A3BX/
    Alice-4F2X_final.mp4
    Bob-9KL3_final.mp4
    assembly_report.txt    ← check for any gaps

# Clean up server
ssh root@YOUR_IP
rm -rf /opt/openbooth/chunks/OB-20260306-A3BX

# Tell participants to clear their browser cache (open recorder page → browser console)
clearCache()
```

---

## Assembler

```bash
# Auto-detect all participants
python3 assemble.py OB-20260306-A3BX

# Custom directories
python3 assemble.py OB-20260306-A3BX --chunks-dir ~/Downloads --output-dir ~/Podcasts

# Specific participants only
python3 assemble.py OB-20260306-A3BX --participants Alice-4F2X,Bob-9KL3

# Requires ffmpeg
brew install ffmpeg
```

The assembler auto-detects all participants, prefers local cache chunks (higher quality) over server chunks where both exist, deduplicates overlapping chunks, and outputs a text report flagging any gaps.

---

## Adding guests

Same URL, different name. Guests type their name on join and get a unique suffix automatically. The assembler picks them up with no extra configuration.

```
# Send the same recorder URL
http://YOUR_IP/recorder.html?session=OB-20260306-A3BX

# Third participant appears automatically in output
sessions/OB-20260306-A3BX/
    Alice-4F2X_final.mp4
    Bob-9KL3_final.mp4
    Charlie-7TK2_final.mp4
```

---

## What participants / guests do

1. Open the recorder URL in Chrome
2. Allow camera and microphone when prompted
3. Type their name → click **Join Session**
4. Click **Start Recording** when the host says go
5. Click **Stop** when done
6. If flagged for a network issue: click **Download Local Cache (Rescue)** and send the files to the host
7. When the host confirms the session is safe: open browser console, run `clearCache()`

No software, no account, no configuration.

---

## Troubleshooting

**Chunks not uploading to server**
- Check the redundancy panel — "no endpoint" means config.js is missing or UPLOAD_ENDPOINT is null
- Health check: `curl http://YOUR_IP/health`
- Live server logs: `ssh root@YOUR_IP` then `journalctl -u openbooth -f`
- Local cache is always running regardless of upload status

**Gap detected in assembly**
- Check `assembly_report.txt` for which chunk indices are missing
- Ask the affected participant to click Rescue Download
- Add rescue files to the chunks folder and re-run assembler

**Chrome asks for camera permission every time**
- Expected when opening files locally (`file://`)
- Hosting on the droplet fixes this — permissions persist per domain

**WebM output instead of MP4**
- Firefox outputs WebM, Chrome outputs MP4
- Assembler re-encodes WebM to MP4 automatically
- All participants should use Chrome for consistent output

**Monitor shows no participants**
- Check SESSION_STATE_URL is set correctly in config.js
- Confirm chunk server is running: `systemctl status openbooth`

---

## Cost

| Component | Monthly cost |
|-----------|-------------|
| DigitalOcean droplet — 1GB | $6/month |
| Everything else | Free |
| **Total** | **$6/month** |

---

## Adding HTTPS later

When you want `https://` instead of `http://`:
1. Register a domain (~$15/year)
2. Point an A record at your droplet IP
3. `apt install certbot python3-certbot-nginx -y`
4. `certbot --nginx -d yourdomain.com`
5. Update UPLOAD_ENDPOINT and SESSION_STATE_URL in `config.js` to `https://`

---

## How to Work Here

This project operates within the [living-systems](https://github.com/tklrstudio/living-systems) constitutional framework. Start with `_context/CHARTER.md` for project boundaries, decision criteria, and governance rules.