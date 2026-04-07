# Codex + Claude Operator Brief

Last updated: 2026-04-03
Purpose: provide a short working guide for using the starter-pack effectively in Codex and Claude Code.

## Default Habit

Use a brief-first flow for anything bigger than a tiny edit:

1. ask for `repo-hygiene` if the repo state is unclear
2. ask for `planner` if the work is ambiguous or multi-step
3. hand one scoped brief to `implementer`
4. ask for `reviewer` after meaningful code changes
5. ask for `docs-handoff` when the work changed durable setup or doctrine

If you edited the starter-pack files themselves:

- edit the canonical templates in `subagent-starter-pack`, not the repo-local copies
- refresh the target repo with `bash ~/.codex/skills/subagent-starter-pack/scripts/install_starter_pack.sh --target "$PWD" --profile generic-v2 --refresh`
- bootstrap the repo validation environment with `./tools/starter-pack/bootstrap_env.sh`
- validate the starter-pack with `.venv/bin/python tools/starter-pack/validate.py`
- start a new Codex session in the repo after refreshing `.codex/config.toml` or `.codex/agents/`
- start a new Claude session or use `/agents` after refreshing `.claude/agents/`

## Prompt Patterns

Planning:

`Use planner first. Scope this into a bounded brief with validation commands and tell me the next implementation thread to run.`

Implementation:

`Use implementer. Execute only the approved step. Do not widen scope. Run the listed validation and report changed files plus blockers.`

Review:

`Use reviewer on this branch versus main. Findings first, no style-only nits.`

Docs:

`Use docs-handoff. Update only the durable docs that now drift from the implemented behavior.`

Hygiene:

`Use repo-hygiene. Tell me whether this is a safe start-state and what must be cleaned up before I proceed.`

## Optional Advanced Orchestration

If a repo has its own planning or execution framework, treat that as an optional overlay. The shared starter-pack is self-contained and should still work without extra global planning or execution skills.

## Other Machines

For first-time setup on another machine, use:

- `docs/starter-pack/setup.md`

That guide covers:

- canonical shared starter-pack files versus repo-owned overlays
- explicit repo refresh after starter-pack updates
- repo-local Python validation bootstrap
- reload behavior
- a first-run verification checklist
