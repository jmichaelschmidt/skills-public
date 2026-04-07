# Operator Brief

Purpose: provide a short working guide for using the starter-pack roles effectively.

## Default Habit

1. ask for `repo-hygiene` if the repo state is unclear
2. ask for `planner` if the work is ambiguous or multi-step
3. hand one scoped brief to `implementer`
4. ask for `reviewer` after meaningful code changes
5. ask for `docs-handoff` when the work changed durable setup or doctrine

For any non-trivial delegated task, make three things explicit:

1. what "done" looks like
2. what context the worker must read first
3. what constraints matter, especially delete, scope, naming, destination, or move limits

## Prompt Patterns

Planning:

`Use planner first. Scope this into a bounded brief. Define done, required context, constraints, validation commands, and the next implementation thread to run.`

Implementation:

`Use implementer. Execute only the approved step. Do not widen scope. Restate the destination and non-destructive constraints if artifacts or files are involved. Run the listed validation and report changed files plus blockers.`

Review:

`Use reviewer on this branch versus main. Findings first, no style-only nits.`

Docs:

`Use docs-handoff. Update only the durable docs that now drift from the implemented behavior. Preserve sources, contradictions, and unanswered questions when the work was research-heavy.`

Hygiene:

`Use repo-hygiene. Tell me whether this is a safe start-state and what must be cleaned up before I proceed.`
