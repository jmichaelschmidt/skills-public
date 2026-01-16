# Skills Marketplace: Public

Freely available skills for anyone

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add jmichaelschmidt/skills-public
```

Then browse and install individual skills via the `/plugin` UI.

## Available Skills

Skills in this marketplace:

| Skill | Description |
|-------|-------------|
| (none yet) | Run `scripts/publish.py <skill> --tier public` to add skills |

## Publishing Skills

To publish a skill to this marketplace:

```bash
~/.claude/skills/skill-manager/scripts/publish.py ~/.claude/skills/my-skill --tier public
```

## Structure

```
skills-public/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace configuration
├── skills/
│   └── (your skills here)
└── README.md
```
