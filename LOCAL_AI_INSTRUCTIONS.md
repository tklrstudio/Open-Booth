# Local AI Instructions — Open Booth

**Purpose:** Workspace-specific context for Open Booth
**Status:** Canonical
**Scope:** This workspace only
**Created:** 2026-03-18
**Last Updated:** 2026-04-28
**Version:** 1.0.0

This is an open-source repo — the `.living-systems/` submodule is not included. Use this file and `_context/CHARTER.md` as primary context.

---

## Scope

**Workspace code:** OB
**Decision prefix:** DEC-OB
branch-strategy: main-only

---

## Context Files

Read these project-specific files:

1. `_context/CHARTER.md` — Project definition, boundaries, quality criteria
2. `temporal/WORK_IN_PROGRESS.md` — What is currently in flight

---

## Implementation Gate

In-session agents design, write briefs, and review results. They do not directly edit source files to implement features or fixes.

**Any edit to a source file** (`.py`, `.js`, `.ts`, `.html`, `.css`, `.sql`, or equivalent) that constitutes a feature, fix, or refactor must be queued as a brief via `enqueue_task` and executed by Smitty.

Narrow exceptions where direct in-session edits are acceptable without a brief:
- Pure documentation commits (`.md` files only)
- Single-line config or environment changes
- Hotfixes where Jason explicitly says "just do it" in the current turn

When in doubt, write the brief.

---

## Enqueueing Blacksmith Tasks

Use the `enqueue_task` MCP tool — never raw SQL INSERTs into `brain.blacksmith_queue`, and never `RemoteTrigger`.

**The brief must be committed and pushed to GitHub before calling `enqueue_task`.** The tool fetches the spec file from GitHub at enqueue time and fails immediately if it isn't found. This is intentional: it eliminates the race condition where Smitty would claim a task before the file was reachable.

If the brief isn't on GitHub yet (e.g. you're working locally), pass `spec_content` inline:
```
enqueue_task(task_name=..., spec_path=..., repo=..., spec_content="<brief text>")
```

---

**End Local AI Instructions — Open Booth**

---

## Merge Strategy

**This is a main-only repo. There are no persistent feature branches.**

- **Always commit and push directly to `main`.** Never create a branch unless the brief explicitly instructs it.
- **Never reuse an existing remote branch.** If you find yourself on a branch (e.g. from a previous session or a `git checkout`), switch back to `main` before committing: `git checkout main && git pull`.
- **Do not open a pull request** unless the brief's Scope section explicitly says to and gives a reason.

The only exception: schema changes at Structural or Breaking tier may use a PR as a review gate — but only when the brief says so explicitly.

The default assumption for any brief that does not mention branches or PRs: commit and push directly to `main`.
