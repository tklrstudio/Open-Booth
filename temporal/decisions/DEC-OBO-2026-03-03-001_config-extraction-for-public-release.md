# Decision: Extract Configuration for Public Release

**Purpose:** Template for recording and tracking architectural and governance decisions
**Status:** Canonical
**Scope:** System
**Created:** 2026-03-03
**Last Updated:** 2026-03-03
**Version:** 1.0.0

<!-- Filename: DEC-OBO-2026-03-03-001_config-extraction-for-public-release.md -->

**Created:** 2026-03-03
**Decision Status:** Proposed
**Decision ID:** DEC-OBO-2026-03-03-001
**Workspace:** Open-Booth
**Branch:** Operations

---

## Problem

Open Booth is ready to be published as a public GitHub repo, but the codebase contains hardcoded values specific to the original author's deployment that would prevent anyone else from using it without reading and editing source files.

**Background:**
The project was built as a working tool first, with the intent to open-source it later. During development, some deployment-specific values were hardcoded directly into source files rather than externalised to configuration. The CHARTER.md already states that environment-specific values should live in `.env` and never be hardcoded — the implementation hasn't caught up yet.

**Current state:**
- `recorder.html:313` hardcodes the upload endpoint to `https://recorder.tklrstudio.com/upload`
- `recorder.html:239` displays "Fresh.Rubber" branding (old project name)
- `recorder.html:666` generates session IDs with `FR-` prefix instead of `OB-`
- `recorder.html:377` uses IndexedDB name `FRRecorder_v2`
- `monitor.html:248` has `SESSION_STATE_URL = null` with no config mechanism
- `docs/VPS_SETUP.md` references `/opt/freshrubber/` paths and `freshrubber` service names throughout
- No `.env.example` file exists despite the charter requiring one
- No client-side config file exists — all values are inline in HTML

A new user cloning the repo would need to read the source code, find these values, and edit them by hand — violating the charter's success criterion that "a podcaster with no technical background can self-host Open Booth in under 30 minutes."

---

## Constitutional Alignment

Which of the 6 systems does this decision touch? Check each that applies.

- [x] **Values** — Craft, Generosity (Tier 2). Publishing clean, usable open-source tooling reflects both values.
  Making the tool genuinely usable by others (not just technically available) is the difference between performative and real generosity.
- [ ] **Temporal** — No specific quarterly commitment, but serves the broader goal of shipping creative tools.
- [x] **Contexts** — Creator. Open Booth is a podcasting tool built within the Creator context.
- [ ] **Foundations** — Not directly affected.
- [ ] **Modes** — Not phase-specific.
- [x] **Algorithms** — **Infinite Refinement** risk: this must be a bounded config extraction, not an excuse to redesign the architecture. The scope is: externalise what's hardcoded, rename old branding, update docs. Nothing more.

---

## Decision

Extract all deployment-specific and user-specific values from source files into configuration files, rename legacy "Fresh Rubber" branding to "Open Booth", and update documentation to match.

**Rationale:**
The charter already mandates this pattern (`.env` for server, no hardcoded values). The client side needs a parallel mechanism — a simple `config.js` file that the HTML loads. This is the minimum viable change to make the repo usable by someone who isn't the original author.

**Alternatives considered:**
1. **Environment variables only (no client config file):** Rejected — client-side HTML files can't read `.env` files. Would require a build step or server-side templating, both of which add complexity the charter explicitly avoids.
2. **Query parameters for all config:** Rejected — forces users to construct long URLs with endpoints, bitrates, etc. Fragile and unfriendly.
3. **Full rewrite with a JS framework and build pipeline:** Rejected — violates the "no installs" and low-cost principles. Massive scope creep.

**Scope:**
- **Changes:** Create `client/config.example.js`, create `.env.example`, update `recorder.html` and `monitor.html` to load config, rename all `freshrubber`/`FR-` references, update `docs/VPS_SETUP.md` paths and service names.
- **Does NOT change:** Server architecture, recording logic, chunked upload mechanism, dual encoder design, any functional behaviour.

---

## Consequences

### Positive
- Anyone can clone the repo, copy the example configs, fill in their values, and run
- Meets the charter's 30-minute self-hosting success criterion
- Eliminates the risk of someone accidentally uploading audio to the original author's server
- Consistent branding throughout (Open Booth / OB everywhere)

### Neutral
- Existing deployment at `recorder.tklrstudio.com` will need its own `config.js` (one-time migration)
- Session IDs change from `FR-*` to `OB-*` — old recordings are unaffected but the prefix convention changes going forward

### Risks
- **Infinite Refinement:** The temptation to keep improving config, add validation, add a setup wizard, etc. Mitigation: strict scope — only externalise what's currently hardcoded. No new features.
- **Config file not loaded:** If a user forgets to create `config.js` from the example, the recorder won't know where to upload. Mitigation: clear error message in the UI when config is missing or endpoint is unset.

---

## Execution Checklist

### 1. Actions
- [ ] Create `client/config.example.js` with all client-side configuration values (upload endpoint, branding, chunk timing, bitrates, session prefix, IDB name)
- [ ] Update `client/recorder.html` to load `config.js` and read values from it, with a clear error if config is missing
- [ ] Update `client/monitor.html` to load `config.js` for the session state URL
- [ ] Rename `Fresh.Rubber` branding to `Open Booth` in `recorder.html`
- [ ] Change session ID prefix from `FR-` to `OB-` in `recorder.html`
- [ ] Rename IndexedDB database from `FRRecorder_v2` to `OBRecorder_v1` in `recorder.html`
- [ ] Create `.env.example` documenting server-side configuration (port, chunks dir, max chunk size)
- [ ] Update `docs/VPS_SETUP.md`: replace all `/opt/freshrubber/` with `/opt/openbooth/`, update service name, update nginx config
- [ ] Add `config.js` to `.gitignore` (user-specific, should not be committed)
- [ ] Update `README.md` with config setup instructions

### 2. Documentation
- [ ] Update `README.md` — add "Configuration" section explaining the config files
- [ ] Update `docs/VPS_SETUP.md` — all paths, service names, and references
- [ ] Update `_context/CHARTER.md` architecture section if file structure changes

### 3. User Guides Required
- [ ] No standalone user guides required — README and VPS_SETUP.md serve this purpose and will be updated in-place

### 4. Cross-References and Subsystem Impact
- [ ] This is a standalone project with no child projects or cross-repo dependencies
- [ ] No living-systems submodule updates required

### 5. Verification
- [ ] `config.example.js` contains every value that was previously hardcoded in source files
- [ ] `recorder.html` fails gracefully with a visible error when `config.js` is missing
- [ ] No remaining references to `freshrubber`, `Fresh.Rubber`, `FRRecorder`, or `FR-` prefix in source files
- [ ] No remaining hardcoded URLs (e.g., `tklrstudio.com`) in source files
- [ ] `.env.example` documents all server configuration options
- [ ] `VPS_SETUP.md` paths and service names are consistent with `openbooth` naming
- [ ] Constitutional alignment confirmed (no system conflicts)

---

## Execution Record

**Executed:** 2026-03-03
**Executed by:** Claude (Opus 4.6)
**Result:** Success

**Notes:**
Executed as planned. Server.py also updated to read `OB_PORT`, `OB_CHUNKS_DIR`, `OB_MAX_CHUNK_MB` from environment variables (falling back to CLI args, then defaults). Both HTML files use nullish coalescing (`??`) to fall back gracefully when config.js is missing — local-only mode works with no config at all.

**Artefacts:**
- Created: `client/config.example.js`
- Created: `.env.example`
- Created: `temporal/decisions/00-proposed/DEC-OBO-2026-03-03-001_config-extraction-for-public-release.md`
- Modified: `client/recorder.html` — config loading, branding, session prefix, IDB name
- Modified: `client/monitor.html` — config loading, notice text
- Modified: `scripts/server.py` — environment variable support
- Modified: `docs/VPS_SETUP.md` — all paths, names, and setup instructions
- Modified: `README.md` — config setup instructions, file table
- Modified: `.gitignore` — added `client/config.js`

**User Guides Created:**
- None required — README and VPS_SETUP.md updated in-place

**Verification results:**
- Grep for `freshrubber`, `Fresh.Rubber`, `FRRecorder`, `tklrstudio`, `'FR-'` across all source files: zero matches (only in this decision doc's problem statement)
- Config loading confirmed: both HTML files load config.js, fall back to empty object, use `??` for all values
- `.env.example` documents all server env vars
- `config.example.js` documents all client config values

**Lessons learned:**
- The VPS_SETUP.md had the old branding scattered across many different contexts (service names, paths, configs, commands) — a bulk replace_all was efficient but required multiple passes for different patterns (`freshrubber`, `sites-available/freshrubber`, `freshrubber.service`, etc.)

---

## Related

**Goals:**
- Ship Open Booth as a usable open-source tool (primary)

**Commitments:**
- Open Booth public release (sizing: Medium)

**Decisions:**
- No prior decisions in this workspace

---

**End of Decision Record**

---

*For workflow procedures (creating, approving, implementing, superseding decisions), see the algorithm files in `constitution/7-algorithms/decision/`. Keep this document proportional — a small decision needs a brief fill-in, not a lengthy analysis.*
