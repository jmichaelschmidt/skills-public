# Skills Marketplace: Public

A free, curated collection of skills for Claude Code and other AI coding assistants.

## What Are Skills?

Skills are instructions that teach AI assistants how to perform specific tasks. When you install a skill, your AI assistant gains new capabilities - like knowing how to deploy to your server, follow your team's coding standards, or use your project's specific tools.

Think of skills like browser extensions, but for AI assistants. They extend what your AI can do.

### Write Once, Use Everywhere

Skills follow the [Agent Skills Specification](https://agentskills.io/specification), an open standard supported by multiple AI coding assistants including Claude Code, OpenAI Codex, Gemini CLI, and GitHub Copilot. This means:

- **One skill works across all platforms** - Write a skill once and use it with any supported AI assistant
- **No vendor lock-in** - Your skills aren't tied to a single tool
- **Portable workflows** - Switch between AI assistants without losing your custom capabilities

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
| [skill-manager](skills/skill-manager/) | Manage, sync, and publish Agent Skills across multiple AI platforms. Write a skill once, then distribute it to Claude Code, Codex, Gemini CLI, and Copilot simultaneously. |

## Trust & Security

### Curated, Not Open

While this is a public repository, **not just anyone can add or modify skills**. All submissions go through a review process before being merged. This marketplace is curated to ensure:

- **No malicious instructions** - We review for prompt injection, data exfiltration attempts, and other security risks
- **No harmful commands** - Skills that run destructive commands must include appropriate warnings and confirmations
- **Transparent behavior** - Skills should do what they claim to do, nothing more
- **Quality standards** - Skills must be well-documented and actually useful

### How We Review Skills

Every pull request is manually reviewed. We check for:

1. **Security risks** - Prompt injection, attempts to override safety guidelines, hidden instructions
2. **Data safety** - No sending user data to external services without clear disclosure
3. **Destructive operations** - Any commands that delete, overwrite, or modify system files must have safeguards
4. **Credential handling** - Skills must not log, transmit, or mishandle sensitive information
5. **Accuracy** - The skill description must match what it actually does

### Your Responsibility

Even with our review process, you should:

- **Read a skill before installing** - Check the SKILL.md to understand what it does
- **Review any scripts** - If a skill includes scripts, inspect them before running
- **Report concerns** - If you notice suspicious behavior, [open an issue](https://github.com/jmichaelschmidt/skills-public/issues)

## How to Contribute

### Proposing a New Skill

We welcome contributions! Here's how to submit a skill:

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

6. **Open a pull request** with:
   - A clear description of what your skill does
   - Example use cases
   - Any security considerations

### Skill Guidelines

Good skills are:

- **Focused** - Do one thing well
- **Clear** - Write instructions the AI can follow unambiguously
- **Safe** - Include warnings for destructive operations; never hide behavior
- **Documented** - Explain what the skill does, when to use it, and any prerequisites
- **Cross-platform** - Avoid hardcoding paths or platform-specific assumptions when possible

### What Will Get Rejected

- Skills that attempt prompt injection or try to override AI safety guidelines
- Skills that send data to external services without clear disclosure
- Skills with obfuscated or hidden functionality
- Skills that are duplicates of existing skills without meaningful improvement
- Low-quality or undocumented skills

## Installing Skills Manually

If you prefer not to use the `/plugin` UI, you can install skills manually:

1. Clone this repo or download a skill folder
2. Copy it to `~/.claude/skills/`
3. Restart Claude Code

For other platforms:
- **Codex**: `~/.codex/skills/`
- **Gemini CLI**: `~/.gemini/skills/`
- **GitHub Copilot**: `~/.copilot/skills/`

Or use the `skill-manager` skill to sync across all platforms automatically.

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
