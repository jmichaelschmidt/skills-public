# PRD Execution Ledger

Use this ledger when a plan has more than 2 threads, any parallelism, or meaningful rollout risk.

```markdown
# Execution Ledger: <Plan Name>

## Goal
- <one-sentence objective>

## Definition Of Done
- <copy the most important done conditions>

## Execution Mode
- Sequential | Wave-based | Hybrid

## Decision Log
- YYYY-MM-DD: <decision or scope change>

## Thread Status

| Thread | Name | Status | Owner | Depends On | Output | Verify | Notes |
|--------|------|--------|-------|------------|--------|--------|-------|
| 1 | <name> | PENDING | worker/orchestrator | - | <path or artifact> | pending | |
| 2 | <name> | BLOCKED | worker | 1 | <path> | pending | waiting on Thread 1 |

## Runnable Now
- Thread <N> - <name>

## Blocked
- Thread <N> - blocked by <dependency>

## Verification Summary
- Thread-level checks:
  - <result>
- Plan-level checks:
  - <result>

## Next Action
- Spawn Thread <N> with <owner> and expected output <artifact>
```

Keep the ledger short. It exists to preserve orchestration state, not to become a second PRD.
