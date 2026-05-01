# Decision: Host-Controlled Recording and Chapter Markers

**Created:** 2026-03-04
**Decision Status:** Proposed
**Decision ID:** DEC-OBO-2026-03-04-002
**Workspace:** Open-Booth
**Branch:** Architecture

---

## Problem

Open Booth currently treats all participants as equal peers — each independently starts and stops their own recording. For real podcast sessions, one person (the host) needs to coordinate: start everyone recording at once, stop everyone, and drop chapter markers for post-production editing.

**Background:**
The charter lists "Multi-participant coordination dashboard" as an in-scope future capability. This implements the first two pieces: centralized start/stop and chapter markers. It stays within charter constraints (no cost increase, no installs, no reliability compromise).

**Current state:**
- No concept of host vs guest — all participants are peers
- No way to coordinate start/stop across participants
- No chapter marker support
- Monitor shows participant state but cannot control anything

---

## Constitutional Alignment

- [x] **Values** — Craft, Generosity (Tier 2). Gives podcasters real production tools without cost or complexity.
- [ ] **Temporal** — No specific commitment.
- [x] **Contexts** — Creator. Podcast coordination is core to the creator context.
- [ ] **Foundations** — Not directly affected.
- [ ] **Modes** — Not phase-specific.
- [x] **Algorithms** — Must not compromise reliability (Design Principle #1). Manual override always available.

---

## Decision

Add host-controlled recording coordination via HTTP polling. The host is determined by a `?role=host` URL parameter. Guests poll for commands every 2 seconds. Chapter markers are stored in session state. Manual recording controls remain fully functional at all times.

**Key design choices:**

1. **Polling over SSE/WebSocket** — Consistent with the existing HTTP-only architecture. 1-2s latency on start/stop is acceptable for podcast recording.

2. **Host via `?role=host` URL param** — Explicit and deterministic. No race conditions, no "who clicked first" ambiguity. Server validates only one host per session.

3. **Manual override always available** — Charter says "reliability first". If command polling fails, guests retain full manual start/stop. Recording never depends on the coordination layer.

4. **Chapter markers in session-state** — No separate endpoint needed for v1. Markers are included in the `/session-state` response.

**Rationale:**
These are the minimum changes to enable coordinated podcast recording. Each choice minimises complexity while delivering real production value.

**Alternatives considered:**
1. **WebSocket/SSE for real-time commands:** Rejected — adds Nginx complexity, persistent connections, failure modes. 2s polling is sufficient.
2. **First-to-join becomes host:** Rejected — race condition prone, non-deterministic.
3. **Separate chapter markers endpoint:** Rejected — adds complexity for v1. Session-state is already polled.

**Scope:**
- **Changes:** `scripts/server.py`, `client/recorder.html`, `client/monitor.html`, `client/config.example.js`, `docs/VPS_SETUP.md`, `_context/CHARTER.md`
- **Does NOT change:** `scripts/assemble.py`, upload/chunk handling, IndexedDB logic, encoding parameters

---

## Consequences

### Positive
- Host can coordinate recording start/stop across all participants
- Chapter markers available for post-production
- Monitor shows host status and chapter timeline
- Manual override ensures reliability is never compromised

### Neutral
- Guests see slightly different UI when host is connected (controlled mode vs manual mode)
- Existing single-user workflows are unaffected (no `?role=host` = no coordination layer)

### Risks
- **Polling adds server load:** Mitigated — 2s polls from a handful of podcast participants is negligible on a $6 droplet
- **Host disconnection:** Mitigated — guests fall back to manual mode, recording continues

---

## Execution Checklist

### 1. Actions

**Server (`scripts/server.py`):**
- [x] Expand SessionState model with host, commands, chapters fields
- [x] Add `register_host()`, `add_command()`, `get_commands_since()` methods
- [x] Add POST `/register` endpoint
- [x] Add POST `/session-command` endpoint (host-only)
- [x] Add GET `/session-commands` endpoint (polling)
- [x] Extend GET `/session-state` response with host, chapters, commandCount
- [x] Add JSON body parsing alongside existing multipart parsing

**Recorder (`client/recorder.html`):**
- [x] Read `?role=host` from URL params at page load
- [x] POST to `/register` after joining
- [x] Derive endpoint URLs from UPLOAD_ENDPOINT
- [x] Host UI: Start All, Stop All, Chapter button + label input
- [x] HOST badge near participant tag
- [x] Guest command polling with 2s interval
- [x] Process start/stop/chapter commands from host
- [x] 3 consecutive poll failures → fall back to manual mode
- [x] Guest UX: "Controlled by host" status line, dimmed buttons
- [x] Host offline detection and warning

**Monitor (`client/monitor.html`):**
- [x] Host indicator in summary bar
- [x] Chapter markers section
- [x] Demo mode updated with sample host and chapter data

**Config and docs:**
- [x] Add COMMAND_POLL_MS to config.example.js
- [x] Add Nginx proxy locations for new endpoints in VPS_SETUP.md
- [x] Add session workflow section to VPS_SETUP.md
- [x] Note partial implementation in CHARTER.md

### 2. Documentation
- [x] `docs/VPS_SETUP.md` — new Nginx locations, workflow section
- [x] `_context/CHARTER.md` — future capabilities note

### 3. Verification
- [ ] curl: Register host, second host registration fails
- [ ] curl: Non-host command rejected
- [ ] curl: Commands poll with since param returns only new commands
- [ ] curl: Session-state includes host and chapters
- [ ] Browser: Host start all → guest auto-starts within 2-3s
- [ ] Browser: Host chapter marker → appears in guest log and monitor
- [ ] Browser: Host stops all → guest auto-stops
- [ ] Browser: Host disconnects → guest sees warning, manual controls work
- [ ] Browser: Server down → guest falls back to manual mode after 3 failed polls

---

## Related

**Goals:**
- Multi-participant coordination dashboard (charter future capability)

**Decisions:**
- **Related to:** DEC-OBO-2026-03-03-001 (config extraction), DEC-OBO-2026-03-04-001 (doc fixes)

---

**End of Decision Record**
