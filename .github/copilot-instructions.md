Read `LOCAL_AI_INSTRUCTIONS.md` and `_context/CHARTER.md` for the context-loading sequence and working rules for this repo.

## Open Brain — Session Management (MANDATORY)

At the start of every session:
1. Call `start_session` (brain-mcp server) with `working_directory` set to the current repo path. Store the `session_id`.
2. Before starting any goal or topic, call `search_memory` (brain-mcp) to retrieve prior context.

After every substantive response, call `log_message` twice:
- `role: "user"`, `content`: the user's message verbatim, `session_id` from above
- `role: "assistant"`, `content`: your response verbatim; set `is_final: true` on the last message of the session
