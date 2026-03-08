# PRD Executor Adoption Notes

`prd-executor` borrows a few strong ideas from `gsd-build/get-shit-done` while staying aligned with the existing markdown PRD workflow.

## Adopted

- The orchestrator owns wave decisions instead of blindly launching all work.
- Execution state is written down in a compact ledger instead of left in chat history.
- Verification is a first-class phase, especially for risky changes.
- Work can run in a fast path for small plans or a guarded path for risky plans.

## Not Adopted

- XML plan files or XML command envelopes
- A custom command framework for every execution action
- Heavy indirection between plan, task, and worker instructions

## Why

The current `prd-planner` output is already strong. The missing piece is disciplined execution, not a new planning language. `prd-executor` keeps the existing PRD format and adds:

- clearer orchestration ownership
- reusable thread prompt packaging
- explicit status tracking
- tighter delegation rules

That preserves the benefits of thread isolation and reasoning economy without introducing a second planning system.
