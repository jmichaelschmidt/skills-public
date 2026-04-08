# Starter-Pack Workflow

Purpose: define the shared operating model for the starter-pack roles in a generic repo.

## Core Model

- keep execution serial by default
- use one bounded role at a time for most implementation work
- use parallel work only for independent review, audit, research, or synthesis passes
- keep the shared prompts self-contained so the starter-pack works without extra machine-level skills

## Role Sequence

1. `repo-hygiene`
2. `planner` when needed
3. `implementer`
4. `reviewer`
5. `security-reviewer` when the surface warrants it
6. `docs-handoff`
7. `repo-hygiene` closeout

## When To Use A Role

- `repo-hygiene`: at task start when Git state, branch ownership, or checkout safety is unclear; again before publication
- `planner`: when the next implementation thread is not decision-complete or the validation path is not yet explicit
- `implementer`: when one approved step can be executed without redefining the plan
- `reviewer`: after non-trivial implementation to look for correctness issues and unproven claims
- `security-reviewer`: when the change touches auth, secrets, shell, network, cron, or permissions
- `docs-handoff`: when the durable operator-facing record now drifts from implemented behavior

## When Not To Use A Role

- do not send simple, fully specified single-step edits to `planner`
- do not send exploratory repo-state questions to `implementer` when `repo-hygiene` or `planner` should go first
- do not ask `reviewer` or `security-reviewer` to rewrite the implementation
- do not ask `docs-handoff` to rewrite doctrine broadly when only one narrow durable update is needed
- do not introduce extra workflow skills as new default roles

## Handoff Expectations

- `planner`: objective, definition of done, required context, explicit constraints, scope, exclusions, references, ordered steps, validation commands, next role
- `implementer`: changed files, validation run, blockers, next review/docs follow-up; restate destination and non-destructive constraints for artifact-heavy work
- `reviewer`: findings first, exact references, missing-test or missing-validation notes
- `docs-handoff`: only the durable updates needed to keep the repo legible; preserve sources, contradictions, and unanswered questions for research-heavy outputs
- `repo-hygiene`: state, risk, and next safe cleanup/bootstrap step

## Briefing Rules

Before delegating meaningful work, define:

- what "done" looks like
- what context or read-first files matter
- what constraints matter

Default constraints to call out when relevant:

- do not delete anything unless deletions are intended
- keep naming or move rules explicit
- state the destination for new artifacts
- say what is out of scope

## Optional Overlays

If the repo has its own planning, execution, release, or documentation workflow, layer that on top locally instead of changing the shared starter-pack prompts.

Those overlays should tighten the workflow, not obscure the shared role triggers or closeout expectations.
