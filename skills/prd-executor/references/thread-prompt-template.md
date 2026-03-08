# Thread Prompt Template

Use this template when spawning a subagent for one thread.

```text
You are executing one bounded thread from an existing implementation plan.

Project bootstrap:
- Repo/workspace: <path>
- Read these before changing anything:
  - <bootstrap doc 1>
  - <bootstrap doc 2>

Thread to execute:
### Thread <N> - <Name> - Reasoning Effort: <level>
- Purpose: <purpose>
- Actions:
  - <action>
    - Verify: <check>
- Reference material:
  - <file:line> - <why>
- Deliverables: <outputs>

Dependency context already completed:
- Thread <M>: <concrete outputs only>

Ownership:
- You own these files/modules: <paths>
- Do not revert unrelated changes.
- You are not alone in the codebase. Adjust to existing edits; do not erase them.

Execution rules:
1. Read the listed references first.
2. Complete only this thread's scope.
3. Run the required verification for this thread.
4. Report changed files and verification results clearly.
5. If blocked, stop and explain the blocker precisely.

Required result format:
- Summary of work completed
- Files changed
- Verification run
- Remaining blockers or follow-ups
```

Keep the prompt thread-local. Do not paste the full PRD unless the thread truly needs it.
