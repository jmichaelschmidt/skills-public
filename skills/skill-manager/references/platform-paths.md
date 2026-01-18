# Platform Paths Reference

Detailed documentation of where Agent Skills are stored across different platforms.

## Platform Overview

| Platform | Status | Standard Adoption |
|----------|--------|-------------------|
| Claude Code | Production | Native support |
| OpenAI Codex | Production | Adopted Agent Skills standard |
| Cursor | Compatible | Uses .cursorrules (similar concept) |

## Claude Code

### Global Skills

**Path:** `~/.claude/skills/`

User-created skills available to all Claude Code sessions.

```
~/.claude/
└── skills/
    ├── my-skill-a/
    │   └── SKILL.md
    └── my-skill-b/
        └── SKILL.md
```

### Marketplace Skills

**Path:** `~/.claude/plugins/marketplaces/<marketplace-name>/skills/`

Skills installed from official or third-party marketplaces.

```
~/.claude/plugins/marketplaces/
└── anthropic-agent-skills/
    ├── .claude-plugin/
    │   └── marketplace.json
    └── skills/
        ├── pdf/
        ├── xlsx/
        ├── docx/
        └── ...
```

### Project Skills

**Path:** `.claude/skills/` (relative to project root)

Skills specific to a project, version-controlled with the codebase.

```
my-project/
├── .claude/
│   └── skills/
│       └── project-specific-skill/
│           └── SKILL.md
├── src/
└── ...
```

### Discovery Priority

Claude Code discovers skills in this order:
1. Project skills (`.claude/skills/`)
2. Global user skills (`~/.claude/skills/`)
3. Marketplace skills (`~/.claude/plugins/marketplaces/*/skills/`)

## OpenAI Codex

### Global Skills

**Path:** `~/.codex/skills/`

User-created skills available to all Codex sessions.

```
~/.codex/
└── skills/
    ├── my-skill-a/
    │   └── SKILL.md
    └── my-skill-b/
        └── SKILL.md
```

### Invocation

- List skills: `/skills` command
- Explicit invoke: `$skill-name` in conversation
- Implicit: Auto-detected from description keywords

## Cross-Platform Considerations

### Identical Structure

The skill directory structure is identical across platforms:

```
skill-name/
├── SKILL.md              # Required
├── scripts/              # Optional
├── references/           # Optional
└── assets/               # Optional
```

### Portable SKILL.md

The frontmatter format is identical:

```yaml
---
name: skill-name
description: Description with WHAT and WHEN triggers.
---

# Instructions here
```

### Scripts Compatibility

Scripts should be platform-agnostic where possible:

```python
#!/usr/bin/env python3
import os

# Detect platform if needed
def get_platform():
    if os.path.exists(os.path.expanduser('~/.claude')):
        return 'claude'
    elif os.path.exists(os.path.expanduser('~/.codex')):
        return 'codex'
    return 'unknown'

# Platform-agnostic home
def get_skills_home():
    platform = get_platform()
    home = os.path.expanduser('~')
    return os.path.join(home, f'.{platform}', 'skills')
```

## Environment Variables

### Claude Code

```
CLAUDE_CONFIG_DIR    # Override ~/.claude location
```

### Codex

```
CODEX_CONFIG_DIR     # Override ~/.codex location (if supported)
```

## Symlink Strategy

For maintaining skills across platforms from a single source:

```bash
# Create source repository
mkdir -p ~/projects/my-skills/skill-a
# ... create SKILL.md and resources

# Symlink to Claude Code
ln -s ~/projects/my-skills/skill-a ~/.claude/skills/skill-a

# Symlink to Codex
ln -s ~/projects/my-skills/skill-a ~/.codex/skills/skill-a
```

Advantages:
- Single source of truth
- Changes propagate instantly
- Version control in one location

Disadvantages:
- Broken symlinks if source moves
- Platform-specific changes not possible

## File System Permissions

### Recommended Permissions

```bash
# Skill directories
chmod 755 ~/.claude/skills/my-skill
chmod 755 ~/.codex/skills/my-skill

# SKILL.md and references
chmod 644 ~/.claude/skills/my-skill/SKILL.md

# Executable scripts
chmod 755 ~/.claude/skills/my-skill/scripts/*.py
chmod 755 ~/.claude/skills/my-skill/scripts/*.sh
```

## Troubleshooting

### Skill Not Discovered

1. Verify SKILL.md exists and has valid frontmatter
2. Check directory permissions
3. Ensure name field matches directory name
4. Restart agent session (some platforms cache skill list)

### Symlink Issues

```bash
# Check if symlink is valid
ls -la ~/.claude/skills/my-skill

# Check target exists
ls -la $(readlink ~/.claude/skills/my-skill)

# Fix broken symlink
rm ~/.claude/skills/my-skill
ln -s /correct/path ~/.claude/skills/my-skill
```

### Permission Denied on Scripts

```bash
# Make scripts executable
chmod +x ~/.claude/skills/my-skill/scripts/*.py
```
