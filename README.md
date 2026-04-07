# Skills Marketplace: Public

A curated marketplace of reusable skills for Claude Code, Codex, and other assistants that follow the Agent Skills format.

This repo has two jobs:

- provide installable skills you can use immediately
- explain the design ideas behind the more opinionated skills so other builders can adapt them

## Who This Is For

This repo is for:

- operators who want practical skills they can install into Claude Code or Codex
- builders who want a reference implementation for agent-team design
- teams that want portable skills rather than assistant-specific one-offs

## Quick Start

### Install Through Claude Code

Add the marketplace once:

```text
/plugin marketplace add <marketplace-owner>/skills-public
```

Then open the plugin browser:

```text
/plugin
```

Install a skill for user scope, then reload Claude Code if needed.

### Manual Install

Clone the repo or copy an individual skill folder into your runtime skill directory:

- Claude Code: `~/.claude/skills/`
- Codex: `~/.codex/skills/`
- Gemini CLI: `~/.gemini/skills/`
- GitHub Copilot: `~/.copilot/skills/`

If you use both Claude and Codex, the intended runtime model is:

- install the runtime copy in `~/.claude/skills/<skill>`
- point `~/.codex/skills/<skill>` at that installed Claude copy

### Starter-Pack Quick Start

After installing `subagent-starter-pack`, refresh a repo from the canonical templates:

```bash
bash ~/.codex/skills/subagent-starter-pack/scripts/install_starter_pack.sh --target "$PWD" --profile generic-v2 --refresh
./tools/starter-pack/bootstrap_env.sh
.venv/bin/python tools/starter-pack/validate.py
```

## What You Get

### Install Surface

The public install surface currently includes:

- [subagent-starter-pack](skills/subagent-starter-pack/) for a portable six-role starter-pack across Claude and Codex
- [prd-planner](skills/prd-planner/) for PRD-grade planning and thread decomposition
- [prd-executor](skills/prd-executor/) for bounded execution of an approved plan
- [skill-manager](skills/skill-manager/) for repo-canonical publishing, marketplace distribution, and runtime install management

### Learning Surface

The docs in [docs/README.md](docs/README.md) explain:

- why the starter-pack uses six core roles
- why the system stays serial by default
- why reusable skills were added instead of more global roles
- how repo refresh differs from machine install
- how research and artifact-heavy work changed the design

## Available Skills

| Skill | Description |
|-------|-------------|
| [prd-executor](skills/prd-executor/) | Execute an existing PRD or implementation plan by acting as the orchestrator. Reads the plan, determines runnable threads, spawns bounded subagents when appropriate, tracks status, integrates results, and verifies completion. |
| [prd-planner](skills/prd-planner/) | Generate structured PRD planning documents optimized for AI-assisted development. Creates discrete, single-conversation tasks with reasoning level estimates to optimize token usage and model selection. |
| [skill-manager](skills/skill-manager/) | Manage repo-canonical skills across marketplaces and runtime installs. Publish released skills, install them into Claude, and mirror Codex to the Claude runtime copy. |
| [subagent-starter-pack](skills/subagent-starter-pack/) | Install a portable six-role starter-pack into any repo, then refresh and validate the repo-local managed files from canonical templates. |

## Why It Is Designed This Way

The starter-pack follows a few non-default opinions:

- roles are capability boundaries, not personality labels
- durable artifacts matter more than chat memory
- validation closes work; execution alone does not
- repo-local managed files should be refreshed from canonical templates, not hand-forked
- parallelism is useful, but bounded sidecars are safer than broad swarms for most repo work

Start here for the reasoning:

- [Design Principles](docs/design-principles.md)
- [Cowork Notes](docs/research/ccforpms-cowork-notes.md)
- [Cowork Implications](docs/research/ccforpms-cowork-implications.md)
- [Operating Instance Lessons](docs/case-studies/operating-instance-lessons.md)
- [Runtime Framework Breakdown](docs/case-studies/runtime-framework-breakdown.md)

## Repo Layout

```text
skills/
  subagent-starter-pack/
  prd-planner/
  prd-executor/
  skill-manager/
docs/
  README.md
  design-principles.md
  research/
  case-studies/
```

- `skills/` is the installable marketplace surface
- `docs/` is the educational surface

## Public And Private Scope

This public repo intentionally publishes only the generic starter-pack core.

It does not include:

- private compatibility profiles
- private migration notes
- repo-specific validation paths
- brand-specific operating docs

That split is intentional. The public version is meant to be portable and teachable.

## Trust And Review

This is a curated marketplace, not an unrestricted prompt dump.

Skills added here should be:

- explicit about what they do
- safe about destructive operations
- structured so the runtime behavior can be reviewed
- portable across assistants when possible

## Learn More

- [Agent Skills Specification](https://agentskills.io/specification)
- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
