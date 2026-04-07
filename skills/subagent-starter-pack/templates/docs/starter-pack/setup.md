# Starter-Pack Setup

Purpose: explain how to install, refresh, validate, and reload the generic starter-pack in any repo.

## Install Or Refresh

From the repo root:

```bash
bash ~/.codex/skills/subagent-starter-pack/scripts/install_starter_pack.sh --target "$PWD" --profile generic-v2 --refresh
```

## Bootstrap Validation Environment

```bash
./tools/starter-pack/bootstrap_env.sh
```

## Validate

```bash
.venv/bin/python tools/starter-pack/validate.py
```

To validate unpublished source changes from a local source checkout:

```bash
.venv/bin/python tools/starter-pack/validate.py \
  --starter-pack-skill-dir /path/to/source-repo/skills/subagent-starter-pack
```

## Reload Behavior

- Codex: start a new session after refreshing `.codex/config.toml` or `.codex/agents/`
- Claude Code: start a new session or use `/agents` after refreshing `.claude/agents/`

## Managed Surface

The shared starter-pack manages:

- `AGENTS.md`
- `.codex/config.toml`
- `.codex/agents/`
- `.claude/agents/`
- `docs/starter-pack/`
- `tools/starter-pack/`

Do not hand-edit those files as independent forks.

Optional shared reference:

- `docs/starter-pack/artifact-workflows.md` describes an advisory `inbox / processed / outputs / reference` contract for non-code, artifact-heavy work. Use it only when the repo actually has that kind of workflow.
