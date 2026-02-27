# Open Booth Charter

**Purpose:** A reliable, low-cost, browser-based podcast recording tool for independent podcasters
**Status:** Canonical
**Workspace Code:** OB
**Created:** 2026-02-26
**Last Updated:** 2026-02-26
**Version:** 1.0.0

---

## Purpose

Open Booth exists because independent podcasters deserve a recording tool that is genuinely reliable, costs almost nothing to run, and doesn't force them into specific call software or subscription fees. It was built by a podcaster who experienced data loss with paid tools and decided to fix the problem rather than keep paying for it.

Open Booth is **open source**. Anyone can use it, self-host it, modify it, or build on it. A hosted tier exists for people who want it to just work without setting up a server.

---

## Success Criteria

- A podcaster with no technical background can self-host Open Booth in under 30 minutes using the docs (or with AI assistance from the docs)
- A recording session completes without data loss
- If anything fails, the user knows immediately — what failed, what was recovered, what may be missing
- The hosted tier runs on a $6/month DigitalOcean droplet
- The repo README and docs are clear enough that an AI assistant can guide a non-technical user through setup without additional context

---

## Boundaries

What Open Booth is **NOT**:

- **Not a replacement for call software** — Open Booth records what the microphone hears; it does not capture other participants or integrate with Zoom, Teams, Meet, etc.
- **Not a complex platform** — no user accounts, no dashboards, no billing infrastructure. Keep it simple enough to self-host on the cheapest viable VPS.

---

## Design Principles

In priority order:

1. **Reliability first** — silent failure is not acceptable. The user must know what happened.
2. **Software-agnostic** — works alongside any call software. Records the microphone. That's it.
3. **Low cost** — $6/month droplet is a constraint, not a starting point. Don't introduce dependencies that increase this.
4. **No installs** — browser-based. A URL is enough. Guests install nothing.
5. **High quality output** — low cost does not mean low quality. Sensible defaults, appropriate bit rates.
6. **Honest failure** — if something goes wrong, say so clearly and completely.
7. **AI-friendly docs** — written so a non-technical user can get help from an AI assistant without additional context.

---

## Architecture

```
open-booth/
├── client/
│   ├── recorder.html     # Recording interface — runs in browser, dual encoder, IndexedDB local storage
│   └── monitor.html      # Session monitoring — real-time upload status and QA
└── scripts/
    └── chunk_server.py   # Lightweight Python server — receives and stores audio chunks
```

**Key decisions:**
- Chunked upload over continuous stream — dropped connection only risks the current chunk
- IndexedDB local storage — chunks stored locally as recorded, independent of upload success
- Dual encoders — two simultaneous encoding streams for redundancy at the capture layer
- No WebRTC — each participant runs their own recorder; no attempt to capture remote audio

**Configuration:** Environment-specific values (server IP, ports) live in `.env`. Never hardcoded. See `.env.example`.

---

## Quality Criteria

Output is good when:
- It works reliably across multiple consecutive sessions without intervention
- Failure modes are surfaced to the user with enough detail to act
- A new contributor (human or AI) can understand the architecture by reading this charter and the code
- The self-hosting experience matches what the docs describe

---

## Failure Patterns to Watch

- **Scope creep toward SaaS** — any suggestion to add user accounts, billing, or multi-tenant infrastructure should be questioned hard. That is not what this project is.
- **Feature over reliability** — new capabilities should not compromise the core recording and upload loop. If it does, it needs explicit sign-off.
- **Doc drift** — docs must stay current. A feature without documentation is not done.
- **Cost inflation** — any architectural change that increases hosting cost beyond the $6/month target needs explicit justification.

---

## Binding Rules

- Do not hardcode IP addresses, ports, or credentials in source files — use `.env`
- Chunk upload and assembly must remain idempotent — safe to run multiple times
- Errors must be surfaced to the user — no silent failures
- Do not introduce software install requirements for hosts or guests
- Update `.env.example` whenever a new environment variable is introduced
- Update docs whenever behaviour changes

---

## Future Capabilities (In Scope, Not Current Priority)

- Auto-assembly of chunks into final audio file post-session
- Auto-edit (silence removal, level normalisation)
- Transcription
- Platform publishing (push to podcast host)
- Multi-participant coordination dashboard

New capabilities must not compromise reliability, increase hosting cost materially, or introduce install requirements without explicit sign-off.

---

*Open Booth is open source. Built by a podcaster, for podcasters. Review this charter when the scope or architecture changes materially.*
