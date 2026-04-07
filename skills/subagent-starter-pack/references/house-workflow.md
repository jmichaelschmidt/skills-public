# Starter-Pack Workflow

Last updated: 2026-04-03
Purpose: define the shared operating model for the Codex and Claude starter-pack in a generic repo.

## Core Model

This starter-pack uses delegated micro-threads for context isolation and token control, not for maximum concurrency.

Default rules:

- keep execution serial by default
- use one bounded role at a time for most implementation work
- use parallel work only for independent review, audit, research, or synthesis passes
- keep the shared prompts self-contained so the starter-pack works without extra machine-level skills

Reload note:

- the canonical shared agent definitions live in `subagent-starter-pack/templates/`
- refresh repo-local starter-pack files from that canonical source instead of hand-editing the repo copies
- after refreshing `.codex/config.toml` or `.codex/agents/`, start a new Codex session in the repo
- after refreshing `.claude/agents/`, start a new Claude session or use `/agents`
- use `./tools/starter-pack/bootstrap_env.sh` to create the repo-local validation environment
- use `.venv/bin/python tools/starter-pack/validate.py` to validate the starter-pack files with parser-backed checks

## Role Set

- `planner`: scopes multi-step work before implementation starts
- `implementer`: executes one approved unit of work
- `reviewer`: checks correctness, regressions, and missing validation
- `docs-handoff`: compresses context into durable docs, setup notes, or summaries
- `security-reviewer`: audits auth, secrets, shell, network, cron, and permission risk
- `repo-hygiene`: checks start-state and closeout-state for Git and worktree discipline

## Default Sequence

1. `repo-hygiene` preflight
2. `planner` when needed
3. `implementer`
4. `reviewer`
5. `security-reviewer` if the surface warrants it
6. `docs-handoff`
7. `repo-hygiene` closeout

Skip `planner` for tiny, obvious edits. Skip `docs-handoff` when nothing durable changed.

## Handoff Artifacts

Planner brief:

- objective
- definition of done
- scope and exclusions
- read-first references
- ordered actions with inline verification
- validation commands
- next role

Implementer closeout:

- changed files
- validation run
- blockers or residual risk
- whether review, security review, or docs follow-up is still needed

Repo-hygiene report:

- current branch and worktree usage
- whether the repo is dirty
- whether the dirt is in-scope or unrelated
- whether validation is missing
- the next safe bootstrap or cleanup step

## Optional Overlay Workflows

The shared starter-pack is self-contained.

If a repo uses a richer planning, execution, release, or docs workflow, layer that on top locally instead of hard-wiring the shared prompts to a machine-level dependency.

The repo-local starter-pack files are expected to match the installed `subagent-starter-pack` templates unless an explicit override mechanism is added later.
