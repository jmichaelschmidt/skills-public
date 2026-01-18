# Skills Marketplace: Public

A free, open collection of skills for Claude Code and other AI coding assistants.

## What Are Skills?

Skills are instructions that teach AI assistants how to perform specific tasks. When you install a skill, your AI assistant gains new capabilities - like knowing how to deploy to your server, follow your team's coding standards, or use your project's specific tools.

Think of skills like browser extensions, but for AI assistants. They extend what your AI can do.

## Quick Start (5 minutes)

### Prerequisites

- [Claude Code](https://claude.ai/download) installed (the CLI or VS Code extension)
- A terminal or VS Code

### Step 1: Add This Marketplace

Open Claude Code and run:

```
/plugin marketplace add jmichaelschmidt/skills-public
```

This tells Claude Code where to find skills. You only need to do this once.

### Step 2: Browse and Install Skills

Run:

```
/plugin
```

This opens the plugin browser. Use the arrow keys to navigate:
- Go to the **Discover** tab to see available skills
- Select a skill and press Enter to see details
- Choose "Install for you (user scope)" to install it for all your projects

### Step 3: Use Your New Skills

Once installed, the skill is automatically active. Just ask Claude to do something the skill enables. For example, if you installed `skill-manager`, you can say:

> "List all my installed skills"

or

> "Publish my-skill to the public marketplace"

Claude will automatically use the skill's instructions.

## Available Skills

| Skill | Description |
|-------|-------------|
| [skill-manager](skills/skill-manager/) | Manage, sync, and publish Agent Skills across multiple AI platforms (Claude, Codex, Gemini, Copilot) and tiered marketplaces |

## How to Contribute

### Who Can Contribute?

**Everyone is welcome!** This is a public, open-source marketplace. You can:

- **Submit new skills** via pull request
- **Improve existing skills** by opening a PR
- **Report issues** if a skill isn't working
- **Request skills** by opening an issue

### Submitting a New Skill

1. **Fork this repository** on GitHub

2. **Create your skill folder** under `skills/`:
   ```
   skills/
   └── your-skill-name/
       ├── SKILL.md        # Required - the skill instructions
       ├── scripts/        # Optional - helper scripts
       └── references/     # Optional - reference docs
   ```

3. **Write your SKILL.md** with this format:
   ```markdown
   ---
   name: your-skill-name
   description: A short description of what this skill does and when to use it.
   ---

   # Your Skill Name

   Instructions for the AI assistant go here...
   ```

4. **Add your skill to marketplace.json** in `.claude-plugin/`:
   ```json
   "skills": [
     "./skills/existing-skill",
     "./skills/your-skill-name"
   ]
   ```

5. **Update this README** to add your skill to the Available Skills table

6. **Open a pull request** with a description of what your skill does

### Skill Guidelines

Good skills are:

- **Focused** - Do one thing well
- **Clear** - Write instructions the AI can follow unambiguously
- **Safe** - Don't include destructive commands without warnings
- **Documented** - Explain what the skill does and how to use it

### Review Process

All submissions are reviewed before merging. We check for:

- Clarity and usefulness
- No malicious code or instructions
- Proper SKILL.md format
- Updated marketplace.json and README

## Installing Skills Manually

If you prefer not to use the `/plugin` UI, you can install skills manually:

1. Clone this repo or download a skill folder
2. Copy it to `~/.claude/skills/`
3. Restart Claude Code

## Troubleshooting

### "Marketplace not found" error

Make sure you added the marketplace first:
```
/plugin marketplace add jmichaelschmidt/skills-public
```

### Skill not appearing after install

1. Try reloading your IDE window (VS Code: `Cmd+Shift+P` → "Reload Window")
2. In `/plugin`, go to Marketplaces tab and press `u` to update

### "Authentication failed" for private repos

This marketplace is public, so no authentication is needed. If you're trying to add a private marketplace, set `GITHUB_TOKEN` in your environment.

## Learn More

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Agent Skills Specification](https://agentskills.io/specification) - Technical spec for skill authors

## License

Skills in this marketplace are provided as-is. Check individual skill folders for specific licensing.
