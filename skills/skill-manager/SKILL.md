---
name: skill-manager
description: Manage, sync, and publish Agent Skills across multiple AI platforms (Claude, Codex, Gemini, Copilot) and marketplace repositories. Use when users want to list skills, sync between platforms, publish to marketplace keys, mirror canonical skills, audit drift, or set up their environment. Triggers on phrases like "list skills", "sync skills", "publish skill", "skill marketplace", "deploy skill", "audit skills", or "skill inventory".
---

# Skill Manager

Manage repo-canonical Agent Skills across marketplace repositories and runtime install surfaces.

## Core Capabilities

1. **Runtime Install** - Install or refresh released skills into the canonical machine runtime path
2. **Development Sync** - Sync unpublished local skills across Claude Code, OpenAI Codex, Gemini CLI, and GitHub Copilot
3. **Inventory** - Discover and list all skills across platform locations
4. **Publish** - Push skills to tiered GitHub marketplace repositories (private/team/public)
5. **Audit** - Compare skill versions, detect drift, identify inconsistencies
6. **Validate** - Check skill compliance with the Agent Skills specification

## Source of Truth

Skill-manager uses a **repo-canonical** model.

The intended release flow is:

1. author in a git repo checkout
2. publish to a marketplace repo
3. install the published artifact into `~/.claude/skills/<skill>`
4. mirror `~/.codex/skills/<skill>` to the Claude install
5. if the skill materializes repo-local files, run its repo refresh flow separately

Do not treat marketplace caches under `~/.claude/plugins/marketplaces/...` as the canonical runtime path.

`scripts/sync.py` still exists for development-only movement of unpublished local skills. It is not the canonical release/install path.

## Supported Platforms

| Platform | User Skills Path | Detection |
|----------|-----------------|-----------|
| Claude Code | `~/.claude/skills/` | `~/.claude/` exists |
| OpenAI Codex | `~/.codex/skills/` | `~/.codex/` exists |
| Gemini CLI | `~/.gemini/skills/` | `~/.gemini/` exists |
| GitHub Copilot | `~/.copilot/skills/` | `~/.copilot/` exists |

## Quick Start

### First-Time Setup

Run the interactive setup wizard:

```bash
scripts/init.py
```

This will:
1. Detect installed AI platforms on your system
2. Configure which runtime platforms to manage
3. Set the canonical runtime policy (`claude` primary, optional Codex mirror)
4. Set development sync mode for ad hoc unpublished skill syncs
5. Optionally configure marketplace repositories

### Install Released Skills Into Runtime

Install a released skill from a local marketplace clone into the canonical machine runtime path:

```bash
scripts/install-from-marketplace.py --marketplace team --skill my-skill
```

This command:

1. reads the published artifact from the local marketplace clone
2. fully replaces `~/.claude/skills/<skill>`
3. recreates or verifies `~/.codex/skills/<skill>` as a symlink to the Claude install
4. removes stale files that disappeared from the published artifact

Use `--all` to refresh every published skill from a marketplace clone.

### Sync Local Development Skills Between Platforms

For unpublished or branch-only work, you can still sync a local skill directly:

```bash
scripts/sync.py /path/to/local/my-skill --to codex
```

Or sync all skills from a specific runtime platform:

```bash
scripts/sync.py --all --from-platform claude
```

Options:
- `--to claude,codex,gemini,copilot` - Override target platforms
- `--to auto` - Auto-detect installed platforms
- `--to all` - Sync to all known platforms
- `--mode symlink|copy` - Override development sync mode
- `--from-platform claude|codex|gemini|copilot` - Required for `--all` unless legacy config still sets one
- `--dry-run` - Preview changes without applying
- `--force` - Overwrite existing skills without prompting
- `--all` - Sync all skills from source platform

### List All Skills

```bash
scripts/inventory.py
```

Options:
- `--platform claude|codex|gemini|copilot|all` - Filter by platform
- `--format table|json|yaml` - Output format
- `--verbose` - Show full paths and metadata
- `--source global|project|marketplace` - Include selected source(s), repeatable
- `--exclude-source global|project|marketplace` - Exclude selected source(s), repeatable
- `--global-only|--project-only|--marketplace-only` - Single-source shortcuts
- `--no-marketplace` - Exclude marketplace entries
- `--include-marketplace` - Backward-compatible alias (marketplace is already included by default)

### Inventory Behavior

- Default `scripts/inventory.py` output includes all discovered sources:
  - global skills
  - project skills
  - marketplace skills
- Use source flags only when you want to narrow results.
- Legacy include forms remain supported:
  - `--include-marketplace`
  - `--include marketplace`
  - `--include=marketplace`
## Marketplace System

`skill-manager` works with marketplace keys from `config.json` (for example: `private`, `team`, `public`, `partner`, `enterprise-core`). Keys are identifiers only; repository names and plugin names can be arbitrary.

### Publish a Skill

```bash
scripts/publish.py ~/.claude/skills/my-skill --to team
scripts/publish.py ~/.claude/skills/my-skill --to partner --in-development
```

Standard publish will:
1. Copy the skill to your team marketplace repo
2. Update marketplace.json
3. Validate and refresh the README.md "Available Skills" table entry
4. Push the publish branch to origin
5. Create and merge a PR back to the tracked default branch
6. Sync to other platforms (if configured)

In-development publish (`--in-development`) will:
1. Copy the skill to `skills-in-development/`
2. Skip `marketplace.json` updates (so it is not installable from marketplace)
3. Skip automatic README table updates
4. Create a PR for review

If the source path includes `skills-in-development/`, publish mode is inferred automatically.

If you don't specify `--to`, you'll be prompted to choose.

**README rule:** For standard publishes, the repository README.md must stay current. `publish.py` now validates the "Available Skills" table and updates the skill row automatically. If the README is missing or malformed, publish should fail until the repo documentation is fixed.

### Sync Marketplace Repos

Pull latest from your marketplace repositories:

```bash
scripts/marketplace-sync.py
scripts/marketplace-sync.py --marketplace team
scripts/marketplace-sync.py --status
scripts/marketplace-sync.py --status --marketplace team
scripts/marketplace-sync.py --branch master
scripts/marketplace-sync.py --auto-stash
scripts/marketplace-sync.py --prune-merged
```

`marketplace-sync.py --status` should be your first repo hygiene check. It reports:
- Current checked-out branch versus the tracked default branch
- Ahead/behind drift from `origin/<default-branch>`
- Uncommitted changes
- Extra local branches
- Merged local branches that are safe cleanup candidates

Use `--prune-merged` to delete local branches that are already merged into the tracked branch. Review unmerged extra branches manually before deleting them.

### Mirror Canonical Skills to Another Marketplace

Mirror from a canonical source ref (`tag`, `branch`, or `commit`) into a target marketplace with manifest and README updates:

```bash
scripts/marketplace-mirror.py mirror --from public --to partner --source-ref v1.2.0
scripts/marketplace-mirror.py mirror --from public --to partner --source-ref 8ab12cd --skill skill-manager
scripts/marketplace-mirror.py mirror --from public --to partner --source-ref main --dry-run
```

Generate drift reports at any time:

```bash
scripts/marketplace-mirror.py drift --from public --to partner
scripts/marketplace-mirror.py drift --from public --to partner --source-ref v1.2.0
```

### Audit Runtime Drift

Audit how a skill moves from repo source to marketplace artifact to runtime install:

```bash
scripts/audit-runtime.py my-skill --marketplace team
scripts/audit-runtime.py my-skill --marketplace team --source ~/GitHub/skills-team/skills/my-skill
```

This reports:

- repo source vs marketplace artifact
- marketplace artifact vs Claude runtime copy
- Codex symlink status vs the Claude runtime copy

### Legacy Marketplace Distribution

`marketplace-distribute.py` remains available for advanced or legacy workflows that intentionally symlink marketplace clones into other platform skill directories. It is not the recommended release/install path for Claude plus Codex.

### Audit Skills for Drift

```bash
scripts/audit.py <skill-name>
scripts/audit.py --all
```

### Validate a Skill

```bash
scripts/validate.py <skill-path>
```

### Operator Quick Commands

```bash
# Repo hygiene
scripts/marketplace-sync.py --status
scripts/marketplace-sync.py --prune-merged

# List discovered skills
scripts/inventory.py

# Publish
scripts/publish.py ~/.claude/skills/my-skill --to team

# Install released runtime copy
scripts/install-from-marketplace.py --marketplace team --skill my-skill

# Mirror
scripts/marketplace-mirror.py mirror --from public --to team --source-ref main --skill my-skill

# Runtime audit
scripts/audit-runtime.py my-skill --marketplace team

# Marketplace drift
scripts/marketplace-mirror.py drift --from public --to team
```

### Marketplace Repo Checklist

Run this checklist before and after any marketplace skill update:

1. Run `scripts/marketplace-sync.py --status` and confirm each repo is on its tracked default branch.
2. Confirm each repo is clean and not ahead/behind `origin/<default-branch>`.
3. Run `scripts/marketplace-sync.py --prune-merged` to clear merged local branches.
4. Review any remaining extra local branches and either delete them or keep them intentionally.
5. Publish or mirror the skill.
6. Push the branch and merge it back into the tracked default branch.
7. Re-run `scripts/marketplace-sync.py --status` on the default branch and verify the repo is aligned.
8. Verify the repo `README.md` "Available Skills" table matches the published skills.

## Configuration

Configuration is stored in your user-local config file (created by `scripts/init.py`, typically `~/.config/skill-manager/config.json`):

```json
{
  "platforms": {
    "claude": {
      "enabled": true,
      "user_path": "~/.claude/skills"
    },
    "codex": {
      "enabled": true,
      "user_path": "~/.codex/skills"
    },
    "gemini": {
      "enabled": false,
      "user_path": "~/.gemini/skills"
    },
    "copilot": {
      "enabled": false,
      "user_path": "~/.copilot/skills"
    }
  },
  "runtime": {
    "primary_platform": "claude",
    "codex_mirrors_claude": true
  },
  "development_sync_mode": "copy",
  "sync_mode": "copy",
  "marketplaces": {
    "private": {
      "repo": "https://github.com/your-org/skills-internal",
      "description": "Personal/experimental skills",
      "visibility": "private"
    },
    "team": {
      "repo": "https://github.com/your-org/skills-team",
      "description": "Shared skills for collaborators",
      "visibility": "private"
    },
    "public": {
      "repo": "https://github.com/your-org/skills-public",
      "description": "Freely available skills",
      "visibility": "public"
    }
  },
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "local_repos_path": "~/GitHub"
}
```

### Config Fields

| Field | Description |
|-------|-------------|
| `platforms` | Platform configurations (enabled, runtime path) |
| `runtime` | Canonical runtime policy (primary platform and Codex mirror behavior) |
| `development_sync_mode` | Default mode for ad hoc `sync.py` use |
| `sync_mode` | Legacy alias preserved for backward compatibility |
| `marketplaces` | GitHub repo URLs keyed by marketplace name |
| `owner` | Your name and email for commits |
| `local_repos_path` | Where marketplace repos are cloned |

## Marketplace Repository Structure

Each marketplace repo follows this structure:

```
<repository-name>/
├── .claude-plugin/
│   └── marketplace.json    # Plugin catalog
├── skills/
│   ├── skill-one/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── skill-two/
│       └── SKILL.md
├── skills-in-development/  # Optional: excluded from marketplace manifest
│   └── alpha-skill/
│       └── SKILL.md
└── README.md
```

### marketplace.json Format

```json
{
  "name": "skills-team",
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "metadata": {
    "description": "Shared skills for collaborators",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "skills-team",
      "description": "Shared skills for collaborators",
      "source": "./",
      "strict": false,
      "skills": [
        "./skills/skill-one",
        "./skills/skill-two"
      ]
    }
  ]
}
```

## Workflow: Publishing Skills

### Step 1: Develop Locally

Create and test your skill in a git repo checkout:

```
my-skill/
├── SKILL.md           # Required
├── scripts/           # Optional
├── references/        # Optional
└── assets/            # Optional
```

### Step 2: Validate

```bash
scripts/validate.py /path/to/repo/skills/my-skill
```

### Step 3: Publish

```bash
scripts/publish.py /path/to/repo/skills/my-skill --to team
# For alpha/in-progress skills that should not be marketplace-installable:
scripts/publish.py /path/to/repo/skills/my-skill --to team --in-development
```

### Step 4: Merge PR

Review and merge the PR created in your marketplace repo.

### Step 5: Install Runtime Copy

Refresh the canonical machine runtime copy from the published marketplace artifact:

```bash
scripts/install-from-marketplace.py --marketplace team --skill my-skill
```

If the machine uses Codex, this command should also verify or recreate the Codex symlink to the Claude runtime copy.

## Cross-Platform Skill Development

### Writing Portable Skills

- Avoid hardcoding platform-specific paths
- Use environment detection if behavior must differ
- Test on multiple platforms before publishing

### Development Sync Modes

| Mode | Pros | Cons |
|------|------|------|
| **copy** | Safe for unpublished development syncs | Must re-sync to propagate changes |
| **symlink** | Useful for advanced/temporary local workflows | Not the recommended release runtime model |

### Skill Specification Compliance

| Field | Required | Max Length | Rules |
|-------|----------|------------|-------|
| `name` | Yes | 64 chars | Lowercase, hyphens, digits only |
| `description` | Yes | 1024 chars | No angle brackets. Include WHAT and WHEN |
| `license` | No | - | License name or file reference |

## Troubleshooting

### Skill Not Appearing After Publish

1. **Merge the PR** - Skills only appear after the PR is merged
2. **Refresh marketplace** - In `/plugin` UI, go to Marketplaces tab and press `u` to update
3. **Verify marketplace.json** - Check that the skill path is in the plugins array

### Sync Not Working

1. Check your config: `cat ~/.config/skill-manager/config.json`
2. Verify target platforms are enabled: look for `"enabled": true`
3. If using `--all`, pass `--from-platform` or set a runtime primary platform
4. Run with `--dry-run` to preview: `scripts/sync.py --all --from-platform claude --dry-run`

### Platform Not Detected

1. Ensure the platform is installed and has its config directory
2. Check paths in config.json match your system
3. Re-run `scripts/init.py` to reconfigure

### Publish Fails

1. Check that `gh` CLI is installed and authenticated
2. Verify repository URLs in config.json
3. Run `scripts/marketplace-sync.py --status` to check repo state

### Codex Mirror Issues

```bash
# Check runtime install
ls -la ~/.claude/skills/my-skill

# Check Codex mirror
ls -la ~/.codex/skills/my-skill
```

## IDE Reload Reminder

After syncing or publishing skills, you may need to reload your IDE window for changes to take effect:

- **VS Code**: `Cmd+Shift+P` → "Reload Window"
- This is required because AI assistants load their skill inventory at startup

## See Also

- `skill-creator` skill - For creating new skills from scratch
- [Agent Skills Specification](https://agentskills.io/specification) - Full specification
