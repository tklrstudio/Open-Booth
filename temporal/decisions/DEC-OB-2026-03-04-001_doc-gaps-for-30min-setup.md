# Decision: Fix Doc Gaps for 30-Minute Setup and AI-Assisted Deployment

**Purpose:** Template for recording and tracking architectural and governance decisions
**Status:** Canonical
**Scope:** System
**Created:** 2026-03-04
**Last Updated:** 2026-03-04
**Version:** 1.0.0

<!-- Filename: DEC-OB-2026-03-04-001_doc-gaps-for-30min-setup.md -->

**Created:** 2026-03-04
**Decision Status:** Approved
**Decision ID:** DEC-OB-2026-03-04-001
**Workspace:** Open-Booth
**Branch:** Operations

---

## Problem

After publishing Open Booth publicly and extracting config (DEC-OB-2026-03-03-001), we assessed the repo against two charter success criteria:

1. "A podcaster with no technical background can self-host Open Booth in under 30 minutes using the docs (or with AI assistance from the docs)"
2. "The repo README and docs are clear enough that an AI assistant can guide a non-technical user through setup without additional context"

Both criteria are close but not met.

**Background:**
The VPS setup guide was written for a single user who already had the files. Now that the repo is public, new users need to get the code first — and the docs don't explain how.

**Current state:**
- VPS_SETUP.md has no "get the code" step — it starts at "create a DigitalOcean account" and assumes files exist at `~/Downloads/`
- Upload paths (`scp ~/Downloads/server.py ...`) don't match either a git clone or a ZIP download
- Step numbering has a gap (Part 9 jumps from Step 18 to Step 20) after config extraction removed the old HTML editing steps
- Troubleshooting still says "Check UPLOAD_ENDPOINT in recorder.html" instead of "in config.js"
- Region is hardcoded to "Sydney" — users elsewhere would need to know to change it
- Charter architecture section references `chunk_server.py` (doesn't exist) and doesn't mention `config.example.js` or `assemble.py`
- No guidance on clone vs download ZIP — the two paths result in different directory structures, which affects every scp command

---

## Constitutional Alignment

Which of the 6 systems does this decision touch? Check each that applies.

- [x] **Values** — Craft, Generosity (Tier 2). Docs that actually work for strangers, not just the author.
- [ ] **Temporal** — No specific commitment.
- [x] **Contexts** — Creator. Open Booth is a podcasting tool.
- [ ] **Foundations** — Not directly affected.
- [ ] **Modes** — Not phase-specific.
- [x] **Algorithms** — **Infinite Refinement** risk: this is documentation polish, not feature work. Must stay bounded to the six identified gaps. No new features, no restructuring.

---

## Decision

Fix all six documentation gaps so the VPS setup guide is self-contained from "I found this repo" to "I'm recording a podcast."

Specifically:
1. Add a "Get the code" section with clone vs download ZIP, explaining how each affects file paths
2. Use a `$OB` variable in all scp commands so they work regardless of how the user got the files
3. Renumber all steps sequentially
4. Fix the stale troubleshooting reference (recorder.html → config.js)
5. Make the DigitalOcean region a choice, not hardcoded Sydney
6. Update the charter architecture section to match actual files

**Rationale:**
These are the minimum changes to meet the charter's own success criteria. Each gap was identified by walking through the docs as a new user would.

**Alternatives considered:**
1. **Write a separate quickstart guide:** Rejected — adds a second document to maintain. The VPS guide should be self-sufficient.
2. **Add a setup script that automates deployment:** Rejected — useful but out of scope. This decision is about docs, not tooling.

**Scope:**
- **Changes:** `docs/VPS_SETUP.md` (bulk), `_context/CHARTER.md` (architecture section only).
- **Does NOT change:** Source code, config files, README.md, server behaviour, recording behaviour.

---

## Consequences

### Positive
- A non-technical user (or AI assistant) can follow VPS_SETUP.md from zero to working deployment without external context
- Clone and ZIP users both have correct paths without guessing
- Charter architecture matches actual repo

### Neutral
- Existing users of the guide will see reorganised step numbers

### Risks
- **Infinite Refinement:** The temptation to keep polishing docs. Mitigation: strict scope — only the six identified gaps.

---

## Execution Checklist

### 1. Actions
- [x] Add Part 0 to VPS_SETUP.md: "Get the code" with clone vs ZIP options, define `$OB` variable
- [x] Explain what changes between clone and ZIP (directory name, presence of git history, path structure)
- [x] Replace all `~/Downloads/...` scp paths with `$OB/scripts/...`, `$OB/client/...` equivalents
- [x] Renumber all steps sequentially (no gaps)
- [x] Fix troubleshooting: "Check UPLOAD_ENDPOINT in recorder.html" → "in config.js"
- [x] Change region from "Sydney" to user's choice with examples
- [x] Update charter architecture section: `chunk_server.py` → `server.py`, add `config.example.js` and `assemble.py`
- [x] Update charter Configuration line to mention both `config.js` (client) and `.env` (server)

### 2. Documentation
- [x] `docs/VPS_SETUP.md` — all changes above
- [x] `_context/CHARTER.md` — architecture section

### 3. User Guides Required
- [x] No standalone user guides required — VPS_SETUP.md is the user guide

### 4. Cross-References and Subsystem Impact
- [x] No cross-repo impact

### 5. Verification
- [x] Grep for `~/Downloads/` in docs — should only appear in the ZIP option explanation, not in scp commands
- [x] Grep for `chunk_server.py` — zero matches across repo
- [x] Step numbers are sequential with no gaps
- [x] Stale troubleshooting reference is fixed
- [x] Constitutional alignment confirmed (no system conflicts)

---

## Execution Record

**Executed:** 2026-03-04
**Executed by:** Claude (AI-assisted)
**Result:** Complete — all six gaps closed

**Notes:**
- VPS_SETUP.md rewritten with Part 0 ("Get the code"), $OB variable throughout, sequential Steps 1–21
- Charter architecture section updated to match actual repo files
- No source code, config files, or README changes (as scoped)

**Artefacts:**
- `docs/VPS_SETUP.md` — bulk update
- `_context/CHARTER.md` — architecture section update

**User Guides Created:**
None required — VPS_SETUP.md is the user guide

**Verification results:**
- `~/Downloads/` in docs: only in ZIP explanation (Step 2), not in scp commands — PASS
- `chunk_server.py` across repo: zero matches outside this decision doc — PASS
- Step numbers: 1–21 sequential, no gaps — PASS
- Stale troubleshooting reference: fixed (now says config.js) — PASS
- Constitutional alignment: no system conflicts — PASS

**Lessons learned:**
None — straightforward documentation fix, scope held

---

## Related

**Goals:**
- Ship Open Booth as a usable open-source tool (primary)

**Commitments:**
- Open Booth public release (sizing: Minor — documentation only)

**Decisions:**
- **Related to:** DEC-OB-2026-03-03-001 (config extraction — this decision closes the remaining gaps from that release)

---

**End of Decision Record**

---

*For workflow procedures (creating, approving, implementing, superseding decisions), see the algorithm files in `constitution/7-algorithms/decision/`. Keep this document proportional — a small decision needs a brief fill-in, not a lengthy analysis.*
