# Starter-Pack Multi-Machine Setup

Last updated: 2026-04-03
Purpose: bootstrap the Codex and Claude starter-pack on another machine without depending on a personal repo layout.

## What This Covers

This guide covers:

- installing the shared starter-pack skill on another machine
- refreshing a target repo from the default `generic-v2` profile
- validating that the repo-local managed files still match the shared source of truth

## Prerequisites

Before using the starter-pack on another machine, confirm:

- Codex is installed and the target repo is trusted
- Claude Code is installed
- the target repo checkout exists
- `~/.codex/skills/subagent-starter-pack/SKILL.md` or `~/.claude/skills/subagent-starter-pack/SKILL.md` exists
- `python3` is available

## Repo-Scoped Vs Machine-Scoped Assets

Repo-scoped managed assets for `generic-v2`:

- `AGENTS.md`
- `.codex/config.toml`
- `.codex/agents/`
- `.claude/agents/`
- `docs/starter-pack/`
- `tools/starter-pack/`

Machine-scoped prerequisites:

- Codex installation and trusted repo state
- Claude Code installation
- repo-local Python validation environment

Shared-source rule:

- the repo-local managed starter-pack files are refreshed artifacts from `subagent-starter-pack/templates/`
- update the shared templates in the source repo first, then refresh the repo
- do not hand-edit repo-local managed starter-pack files as independent forks

## Bootstrap Commands

From the repo root, run:

```bash
bash ~/.codex/skills/subagent-starter-pack/scripts/install_starter_pack.sh --target "$PWD" --profile generic-v2 --refresh
```

Then bootstrap the validator environment:

```bash
./tools/starter-pack/bootstrap_env.sh
```

Then validate:

```bash
.venv/bin/python tools/starter-pack/validate.py
```

If you are validating unpublished source changes from a local source checkout, point the validator at that source explicitly:

```bash
.venv/bin/python tools/starter-pack/validate.py \
  --starter-pack-skill-dir /path/to/source-repo/skills/subagent-starter-pack
```

## How Codex And Claude Pick Up The Starter-Pack

Codex:

- reads repo-scoped instructions from `AGENTS.md`
- reads repo-scoped agent config from `.codex/config.toml`
- reads custom agents from `.codex/agents/`
- expects those repo-local files to be refreshed from the canonical starter-pack templates when the shared role set changes

Claude Code:

- reads project subagents from `.claude/agents/`
- expects the repo-local project agent files to be refreshed from the canonical starter-pack templates when the shared role set changes

## Reload Behavior

After refreshing starter-pack files:

- Codex: start a new Codex session in the repo
- Claude Code: start a new Claude session or use `/agents` to reload project agents

## First-Run Verification Checklist

The target machine is ready when all of these are true:

- the bootstrap command created `.venv`
- the validation command exits successfully
- the validation command confirms the repo-local starter-pack files still match the canonical installed skill
- Codex can see the custom roles in `.codex/agents/`
- Claude can see the project agents in `.claude/agents/`
- the shared docs are present under `docs/starter-pack/`

## Failure Modes

### Validator says TOML or YAML parser dependency is missing

Fix:

- rerun `./tools/starter-pack/bootstrap_env.sh`
- use `.venv/bin/python`, not `/usr/bin/python3`, for validation

### Validator says starter-pack skill is missing or canonical files drifted

Check:

- `~/.codex/skills/subagent-starter-pack/SKILL.md` or `~/.claude/skills/subagent-starter-pack/SKILL.md` exists
- the repo was refreshed with `bash ~/.codex/skills/subagent-starter-pack/scripts/install_starter_pack.sh --target "$PWD" --profile generic-v2 --refresh`
- you did not hand-edit repo-local managed starter-pack files
- if you are validating unpublished starter-pack source changes, rerun the validator with `--starter-pack-skill-dir`

### Codex or Claude does not pick up the new agents

Fix:

- start a new session after refreshing starter-pack files
- confirm you are inside the repo checkout that contains `AGENTS.md`, `.codex/`, and `.claude/`

## Expected Resting State

After setup, another machine should be able to:

- use the same repo-scoped roles and docs
- validate the starter-pack locally with parser-backed checks
- work without any personal repo checkout or repo-specific compatibility docs present
