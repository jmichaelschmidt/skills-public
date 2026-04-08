# Repository Agent Workflow

This repository uses a shared starter-pack of specialized agents for Codex and Claude Code.

This file is a managed starter-pack artifact. Update the canonical `subagent-starter-pack` templates and refresh the repo instead of hand-editing this copy.

## Role Set

- `planner`: scopes multi-step work before implementation starts
- `implementer`: executes one approved unit of work
- `reviewer`: checks correctness, regressions, and missing validation
- `docs-handoff`: compresses context into durable docs, setup notes, or summaries
- `security-reviewer`: audits auth, secrets, shell, network, cron, and permission risk
- `repo-hygiene`: checks start-state and closeout-state for worktree/git discipline

## When To Use Each Role

- `repo-hygiene`: when repo state is unclear, before implementation starts, and before commit, push, or merge
- `planner`: when the work is ambiguous, risky, or multi-step and the next execution thread is not already decision-complete
- `implementer`: when one bounded unit of work is approved and the target files or outputs are clear
- `reviewer`: after meaningful implementation work when correctness, regressions, or validation gaps need a read-only pass
- `security-reviewer`: when auth, secrets, shell, network, cron, or permissions changed, or should have changed but may have been skipped
- `docs-handoff`: when durable setup, workflow, doctrine, or operator-facing behavior changed

## When Not To Change The Model

- do not replace the six roles with a growing catalog of overlapping personas
- do not treat workflow skills as default substitutes for `planner`, `implementer`, or `reviewer`
- do not skip `repo-hygiene` when repo state or checkout ownership is unclear
- do not default to parallel implementation when serial bounded work is sufficient

## Default Workflow

1. Run `repo-hygiene` when starting a task in a Git repo or before publication.
2. Use `planner` for ambiguous, high-risk, or multi-step work.
3. Hand one bounded brief to `implementer`.
4. Use `reviewer` by default after substantial code changes. Add `security-reviewer` when auth, secrets, shell execution, cron, infra, or permissions changed.
5. Use `docs-handoff` when the work changed doctrine, runbooks, plans, setup behavior, or operator-facing guidance.
6. Run `repo-hygiene` again before commit, push, or merge.

## Handoff Contract

- `planner` output: objective, definition of done, required context, explicit constraints, scope, exclusions, reference files, ordered steps with inline verification, validation commands, and recommended next role
- `implementer` output: changed files, validation run, blockers, and whether review/docs follow-up is required; for artifact-heavy work, restate destination paths plus non-destructive constraints
- `reviewer` output: findings first, with concrete file references and test gaps
- `docs-handoff` output: only the durable updates needed to keep the repo legible; preserve sources, contradictions, and unanswered questions when the work is research-heavy
- `repo-hygiene` output: branch/worktree state, validation gap, and cleanup recommendation

## Briefing Contract

For any non-trivial delegated task, make these explicit before work starts:

- what "done" looks like
- what context the worker must read first
- what constraints matter, especially deletion, scope, naming, destination, or move limits

## Advanced Workflows

- The shared starter-pack is self-contained. Repos may layer richer planning, execution, or release workflows on top locally.
- Those overlays should support the shared role contract rather than replace it.
- Do not hard-wire machine-level dependencies into the shared starter-pack files.

## Delegation Rules

- Default to serial delegated micro-threads for context isolation and token control.
- Use parallel work only for independent review, audit, research, or synthesis passes.
- Do not start implementation from a dirty primary checkout.
- If repo state is unclear, stop and route through `repo-hygiene` before coding.

## References

- `docs/starter-pack/workflow.md`
- `docs/starter-pack/operator-brief.md`
- `docs/starter-pack/artifact-workflows.md`
- `docs/starter-pack/setup.md`
- `docs/starter-pack/repo-hygiene-policy.md`
- `docs/starter-pack/security-review-policy.md`
