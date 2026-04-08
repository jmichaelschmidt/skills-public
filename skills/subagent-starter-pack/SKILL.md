---
name: subagent-starter-pack
description: Use when you need to set up or maintain a shared Codex and Claude Code starter-pack for planner, implementer, reviewer, docs-handoff, security-reviewer, and repo-hygiene roles across repos or machines.
---

# Subagent Starter Pack

Use this skill when the user wants a portable starter-pack that can be installed on another machine, refreshed into any repo, or maintained as a generic shared role pack for Claude Code and Codex.

## Core Contract

This skill defines the shared runtime contract for the starter-pack:

- keep the same six roles as the default operating model
- keep execution serial by default
- allow repo-local workflow overlays only as helpers layered on top of the shared role set

This skill owns:

- canonical shared role definitions
- canonical shared starter-pack docs under the generic `v2` contract
- bootstrap and validation tooling for managed repo files
- the installer and refresh path for repo-local managed files

This skill does not own:

- repo-specific manifests
- repo-specific architecture docs, runbooks, or deployment policies
- repo-local overlays that intentionally extend the starter-pack without changing canonical managed files

Optional overlays are acceptable when a repo needs richer planning, execution, or release mechanics, but they should support the shared role contract instead of replacing it.

## Read First

Read these references in order:

- `references/multi-machine-setup.md`
- `references/operator-brief.md`
- `references/house-workflow.md`
- `references/repo-owned-integration-checklist.md`

## Profiles

- `generic-v2`: default repo-independent contract for new repos

## Workflow

1. Confirm whether the task is installation, refresh, validation, or shared-template updates.
2. Treat `templates/` as the canonical source of truth for `generic-v2`.
3. If installing into a new repo, run `scripts/install_starter_pack.sh --target /path/to/repo --profile generic-v2 --dry-run` first.
4. If refreshing an existing repo after shared starter-pack changes, run `scripts/install_starter_pack.sh --target /path/to/repo --profile generic-v2 --refresh`.
5. Do not hand-maintain repo-local managed starter-pack files as independent forks.
6. Run the repo-local bootstrap and validation commands after installation or refresh.
7. Keep repo-specific doctrine and overlays outside the managed starter-pack surface.

## Output

Return:

- what was installed or refreshed
- which profile was used
- whether the repo was refreshed from canonical starter-pack templates
- what remains repo-owned and requires manual review
- which validation commands ran or still need to run
- any prerequisites still missing on the machine

## Gotchas

- Do not treat repo-local starter-pack files as the source of truth.
- Do not reintroduce hard dependencies on external global planning or execution skills in `generic-v2`.
- Do not silently overwrite repo-specific overlays when refreshing shared managed files.
- Keep serial delegation as the default operating model unless a repo has a documented reason to do otherwise.
- Do not treat optional workflow skills as new default roles.
