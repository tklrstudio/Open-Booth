# Decision: Code Decomposition — Open-Booth

**Decision Status:** Proposed
**Decision ID:** DEC-OBO-2026-04-14-120000
**Workspace:** open-booth
**Branch:** Operations
**Created:** 2026-04-14

---

## Problem

Several source files exceed the living-systems line-limit standard (code_authoring.md). This was identified during the 2026-04-14 fleet compliance audit.

**Files exceeding limits:**
- `client/recorder.html`: 938 lines (limit 150)
- `client/monitor.html`: 549 lines (limit 150)
- `scripts/server.py`: 517 lines (limit 400)

**Current state:** Files are oversized, making them harder to navigate, test, and hand off to AI agents with limited context windows.

---

## Decision

Decompose each oversized file into focused modules with single responsibilities, staying within per-file-type line limits.

**Rationale:** Line limits are a constitutional standard (DEC-LS-2026-03-13-002). Compliance enables better AI-assisted development and reduces cognitive load.

**Scope:** Only the files listed above. No behaviour changes — pure structural refactoring.

**Note on HTML files:** `recorder.html` and `monitor.html` are currently single-file browser tools. The recommended approach is to extract inline `<script>` and `<style>` blocks into separate `.js` and `.css` files served alongside the HTML, bringing each file within the 150-line limit.

---

## Execution Checklist

### 1. Code Changes
- [ ] Decompose each listed file into focused sub-modules
- [ ] Verify all imports and references update correctly
- [ ] Run existing tests after each file split

### 2. Verification
- [ ] Re-run `python3 ~/Development/Github/living-systems/tools/fleet_audit.py --repo open-booth` — zero code-limit failures

---

## Implementation Plan

**Execution environment:** local
**Execution approach:** File by file — split largest first, verify tests after each
**Risk level:** Low (structural only, no logic changes)

---

**End of Decision Record**
