# Repo-Owned Integration Checklist

Use this checklist before applying the starter-pack to a repo.

## Stays In The Shared Skill

- the canonical source of truth for the shared starter-pack
- `templates/AGENTS.md`
- `templates/.codex/config.toml`
- `templates/.codex/agents/*.toml`
- `templates/.claude/agents/*.md`
- `templates/docs/starter-pack/*`
- `templates/tools/starter-pack/*`
- the reference docs in this skill

## Stays In The Target Repo

- project-specific manifests
- repo-specific architecture, runbook, or workflow docs outside `docs/starter-pack/`
- project-specific branch conventions, CI flows, deployment instructions, or runtime paths
- any overlays that extend the shared starter-pack without changing canonical managed files

## Default Rule

- repo-local copies of the shared starter-pack files are refreshed artifacts, not primary edit targets
- do not edit repo-local `.codex/agents/`, `.claude/agents/`, `AGENTS.md`, `docs/starter-pack/`, or `tools/starter-pack/` directly
- if a repo truly needs a starter-pack behavior difference, add an explicit override mechanism instead of letting the shared files drift silently

## Required Review Points

Before calling an installation complete, check:

1. The target repo wants the full six-role set rather than a trimmed subset.
2. The repo-local managed starter-pack files were refreshed from the canonical skill templates.
3. Codex and Claude role prompts still point at the correct local starter-pack docs.
4. Validation tooling lives in `tools/starter-pack/` for generic repos, or the legacy path only if the repo has not yet migrated.
5. Repo-specific overlays were updated separately if the repo needs additional docs or manifests beyond the shared starter-pack.

## Machine-Scoped Prerequisites

- Claude Code installed
- Codex installed
- repo-local Python validation environment bootstrapped after install
