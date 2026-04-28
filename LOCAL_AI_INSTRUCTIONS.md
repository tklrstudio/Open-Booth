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

---

## Context Files

Read these project-specific files:

1. `_context/CHARTER.md` — Project definition, boundaries, quality criteria
2. `temporal/WORK_IN_PROGRESS.md` — What is currently in flight

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
