#!/usr/bin/env python3
"""
Skill Publish - Publish skills to marketplace repositories.

Usage:
    publish.py <skill-path> [--to <marketplace>] [options]

Options:
    --to MARKETPLACE    Target marketplace name from config (prompts if not specified)
    --dry-run           Preview changes without applying
    --no-pr             Skip creating a pull request (just push to branch)
    --message MSG       Custom commit message

Examples:
    publish.py ~/.claude/skills/my-skill --to team
    publish.py ./my-skill --to public --dry-run
    publish.py ~/.claude/skills/my-skill --to plumwheel
    publish.py ~/.claude/skills/my-skill  # Will prompt for marketplace
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'


def load_config() -> dict:
    """Load marketplace configuration."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        print("Run 'scripts/init.py' to set up your marketplace configuration.")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config: dict):
    """Save marketplace configuration."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def get_local_repo_path(config: dict, marketplace: str) -> Path:
    """Get the local clone path for a marketplace repo.

    Derives the folder name from the repo URL (e.g., 'skills-team' from
    'https://github.com/org/skills-team').
    """
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'][marketplace].get('repo', '')
    if repo_url:
        # Extract repo name from URL (last part of path, minus .git if present)
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return base_path / repo_name
    # Fallback to default naming if no URL configured
    return base_path / f"skills-{marketplace}"


def validate_source_skill(skill_path: Path) -> tuple:
    """Validate that source is a valid skill directory."""
    if not skill_path.exists():
        return False, f"Source path does not exist: {skill_path}"

    if not skill_path.is_dir():
        return False, f"Source is not a directory: {skill_path}"

    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, f"No SKILL.md found in {skill_path}"

    return True, "Valid skill"


def parse_skill_name(skill_path: Path) -> str:
    """Extract skill name from SKILL.md frontmatter."""
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text()

    if not content.startswith('---'):
        return skill_path.name

    for line in content.split('\n')[1:]:
        if line.startswith('---'):
            break
        if line.startswith('name:'):
            return line.split(':', 1)[1].strip().strip('"').strip("'")

    return skill_path.name


def prompt_for_marketplace(config: dict) -> str:
    """Interactively ask user which marketplace to publish to."""
    marketplaces = config.get('marketplaces', {})
    configured = [(name, info) for name, info in marketplaces.items() if info.get('repo')]

    if not configured:
        print("ERROR: No marketplaces configured with repo URLs.")
        print("Run 'scripts/init.py' to configure your marketplaces.")
        sys.exit(1)

    print("\nWhich marketplace should this skill be published to?")
    for i, (name, info) in enumerate(configured, 1):
        desc = info.get('description', 'No description')
        visibility = info.get('visibility', 'unknown')
        print(f"  {i}. {name} - {desc} ({visibility})")

    name_map = {str(i): name for i, (name, _) in enumerate(configured, 1)}
    name_map.update({name: name for name, _ in configured})

    while True:
        response = input(f"\nSelect marketplace (1-{len(configured)} or name): ").strip().lower()
        if response in name_map:
            return name_map[response]
        else:
            print(f"Invalid selection. Please enter 1-{len(configured)} or marketplace name.")


def run_git_command(args: list, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"Git command failed: git {' '.join(args)}")
        print(f"stderr: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    return result


def ensure_repo_cloned(config: dict, marketplace: str) -> Path:
    """Ensure the marketplace repo is cloned locally."""
    repo_url = config['marketplaces'][marketplace]['repo']
    if not repo_url:
        print(f"ERROR: No repository configured for marketplace '{marketplace}'")
        print(f"Run 'scripts/init.py' to configure your marketplace repositories.")
        sys.exit(1)

    local_path = get_local_repo_path(config, marketplace)

    if local_path.exists():
        # Pull latest
        print(f"Updating local repo: {local_path}")
        run_git_command(['fetch', 'origin'], local_path)
        run_git_command(['checkout', 'main'], local_path, check=False)
        run_git_command(['pull', 'origin', 'main'], local_path, check=False)
    else:
        # Clone
        print(f"Cloning {repo_url} to {local_path}")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['git', 'clone', repo_url, str(local_path)],
            check=True
        )

    return local_path


def update_marketplace_json(repo_path: Path, skill_name: str, skill_description: str, marketplace_name: str, config: dict):
    """Update the marketplace.json to include the new skill."""
    marketplace_json_path = repo_path / '.claude-plugin' / 'marketplace.json'

    if not marketplace_json_path.exists():
        print(f"ERROR: marketplace.json not found at {marketplace_json_path}")
        print("The repository may not be properly initialized as a marketplace.")
        sys.exit(1)

    with open(marketplace_json_path) as f:
        marketplace = json.load(f)

    # Find or create the plugin entry
    plugin_name = f"skills-{marketplace_name}"
    plugin = None
    for p in marketplace.get('plugins', []):
        if p['name'] == plugin_name:
            plugin = p
            break

    if plugin is None:
        # Create new plugin entry
        plugin = {
            'name': plugin_name,
            'description': config['marketplaces'][marketplace_name]['description'],
            'source': './',
            'strict': False,
            'skills': []
        }
        marketplace.setdefault('plugins', []).append(plugin)

    # Add skill if not already present
    skill_path = f"./skills/{skill_name}"
    if skill_path not in plugin.get('skills', []):
        plugin.setdefault('skills', []).append(skill_path)
        plugin['skills'].sort()

    # Bump version
    if 'metadata' in marketplace:
        version = marketplace['metadata'].get('version', '1.0.0')
        parts = version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        marketplace['metadata']['version'] = '.'.join(parts)

    with open(marketplace_json_path, 'w') as f:
        json.dump(marketplace, f, indent=2)

    return marketplace['metadata'].get('version', '1.0.0')


def update_readme(repo_path: Path, skill_name: str, skill_description: str, dry_run: bool = False) -> bool:
    """Update the README.md to include the skill in the Available Skills table.

    Returns True if the README was updated, False if no update was needed.
    For new skills, adds an entry to the table.
    For existing skills, updates the description only if it changed.
    """
    readme_path = repo_path / 'README.md'

    if not readme_path.exists():
        if not dry_run:
            print(f"  Warning: README.md not found at {readme_path}, skipping README update")
        return False

    content = readme_path.read_text()

    # Look for the Available Skills table
    # Format: | [skill-name](skills/skill-name/) | Description |
    table_marker = "## Available Skills"
    if table_marker not in content:
        if not dry_run:
            print(f"  Warning: No '## Available Skills' section found in README.md, skipping")
        return False

    # Truncate description for README table (keep it concise)
    short_description = skill_description
    if len(short_description) > 200:
        # Try to cut at a sentence boundary
        truncated = short_description[:200]
        last_period = truncated.rfind('.')
        if last_period > 100:
            short_description = truncated[:last_period + 1]
        else:
            short_description = truncated.rsplit(' ', 1)[0] + '...'

    # Build the new table row
    new_row = f"| [{skill_name}](skills/{skill_name}/) | {short_description} |"

    # Check if skill already exists in table
    skill_pattern = f"| [{skill_name}]"
    skill_link_pattern = f"[{skill_name}](skills/{skill_name}/)"

    if skill_link_pattern in content:
        # Skill exists - check if description changed
        lines = content.split('\n')
        updated = False
        for i, line in enumerate(lines):
            if skill_link_pattern in line:
                if line.strip() != new_row:
                    lines[i] = new_row
                    updated = True
                    if dry_run:
                        print(f"  [DRY RUN] Would update skill description in README.md")
                    else:
                        print(f"  Updated skill description in README.md")
                break

        if updated and not dry_run:
            readme_path.write_text('\n'.join(lines))
        return updated

    # Skill doesn't exist - add it to the table
    # Find the table and insert in alphabetical order
    lines = content.split('\n')
    table_start = None
    table_header_end = None
    insert_index = None

    for i, line in enumerate(lines):
        if table_marker in line:
            table_start = i
        elif table_start is not None and line.startswith('|'):
            if '----' in line:
                table_header_end = i
            elif table_header_end is not None:
                # This is a skill row - check if we should insert before it
                # Extract skill name from row for alphabetical comparison
                if line.startswith('| ['):
                    existing_skill = line.split('](')[0].replace('| [', '')
                    if skill_name.lower() < existing_skill.lower():
                        insert_index = i
                        break
        elif table_start is not None and table_header_end is not None and not line.startswith('|'):
            # End of table reached, insert at end
            insert_index = i
            break

    if insert_index is None and table_header_end is not None:
        # Insert after the last row we found
        for i in range(len(lines) - 1, table_header_end, -1):
            if lines[i].startswith('|'):
                insert_index = i + 1
                break

    if insert_index is None:
        if not dry_run:
            print(f"  Warning: Could not find proper location in README.md table, skipping")
        return False

    if dry_run:
        print(f"  [DRY RUN] Would add skill to README.md Available Skills table")
    else:
        lines.insert(insert_index, new_row)
        readme_path.write_text('\n'.join(lines))
        print(f"  Added skill to README.md Available Skills table")

    return True


def create_symlink_to_codex(skill_path: Path, skill_name: str, dry_run: bool = False):
    """Create a symlink in the Codex skills directory."""
    codex_skills_dir = Path.home() / '.codex' / 'skills'
    codex_skill_path = codex_skills_dir / skill_name

    if dry_run:
        print(f"  [DRY RUN] Would symlink {codex_skill_path} -> {skill_path}")
        return

    codex_skills_dir.mkdir(parents=True, exist_ok=True)

    if codex_skill_path.exists() or codex_skill_path.is_symlink():
        if codex_skill_path.is_symlink():
            codex_skill_path.unlink()
        else:
            shutil.rmtree(codex_skill_path)

    codex_skill_path.symlink_to(skill_path.resolve())
    print(f"  Symlinked to Codex: {codex_skill_path} -> {skill_path}")


def publish_skill(skill_path: Path, marketplace: str, config: dict,
                  dry_run: bool = False, no_pr: bool = False,
                  custom_message: str = None) -> dict:
    """Publish a skill to the specified marketplace."""

    skill_name = parse_skill_name(skill_path)

    # Read description from SKILL.md
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text()
    description = ""
    if content.startswith('---'):
        for line in content.split('\n')[1:]:
            if line.startswith('---'):
                break
            if line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"').strip("'")

    print(f"\nPublishing skill: {skill_name}")
    print(f"Source: {skill_path}")
    print(f"Marketplace: {marketplace}")

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    results = {
        'skill_name': skill_name,
        'marketplace': marketplace,
        'success': False,
        'pr_url': None,
        'version': None
    }

    # Step 1: Ensure repo is cloned and up to date
    if not dry_run:
        repo_path = ensure_repo_cloned(config, marketplace)
    else:
        repo_path = get_local_repo_path(config, marketplace)
        print(f"  [DRY RUN] Would clone/update repo at {repo_path}")

    # Step 2: Create branch
    branch_name = f"add-{skill_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    if not dry_run:
        run_git_command(['checkout', '-b', branch_name], repo_path)
        print(f"  Created branch: {branch_name}")
    else:
        print(f"  [DRY RUN] Would create branch: {branch_name}")

    # Step 3: Copy skill to repo
    target_skill_path = repo_path / 'skills' / skill_name
    if not dry_run:
        target_skill_path.parent.mkdir(parents=True, exist_ok=True)
        if target_skill_path.exists():
            shutil.rmtree(target_skill_path)
        shutil.copytree(skill_path, target_skill_path)
        print(f"  Copied skill to: {target_skill_path}")
    else:
        print(f"  [DRY RUN] Would copy skill to: {target_skill_path}")

    # Step 4: Update marketplace.json
    if not dry_run:
        new_version = update_marketplace_json(repo_path, skill_name, description, marketplace, config)
        results['version'] = new_version
        print(f"  Updated marketplace.json (version: {new_version})")
    else:
        print(f"  [DRY RUN] Would update marketplace.json")

    # Step 5: Update README.md (optional - only if table exists)
    update_readme(repo_path, skill_name, description, dry_run)

    # Step 6: Commit changes
    commit_message = custom_message or f"Add {skill_name} skill"
    if not dry_run:
        run_git_command(['add', '.'], repo_path)
        run_git_command(['commit', '-m', commit_message], repo_path)
        print(f"  Committed: {commit_message}")
    else:
        print(f"  [DRY RUN] Would commit: {commit_message}")

    # Step 7: Push branch
    if not dry_run:
        run_git_command(['push', '-u', 'origin', branch_name], repo_path)
        print(f"  Pushed branch to origin")
    else:
        print(f"  [DRY RUN] Would push branch to origin")

    # Step 8: Create PR (unless --no-pr)
    if not no_pr and not dry_run:
        try:
            pr_result = subprocess.run(
                ['gh', 'pr', 'create',
                 '--title', f"Add {skill_name} skill",
                 '--body', f"## Summary\n\nAdds the `{skill_name}` skill to the {marketplace} marketplace.\n\n**Description:** {description[:200]}"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if pr_result.returncode == 0:
                pr_url = pr_result.stdout.strip()
                results['pr_url'] = pr_url
                print(f"  Created PR: {pr_url}")
            else:
                print(f"  Warning: Could not create PR via gh CLI: {pr_result.stderr}")
                print(f"  You can create it manually at the repository.")
        except FileNotFoundError:
            print("  Warning: gh CLI not found. Create PR manually.")
    elif not no_pr:
        print(f"  [DRY RUN] Would create PR")

    # Step 9: Symlink to Codex (if enabled)
    if config.get('codex_symlink', True):
        create_symlink_to_codex(skill_path, skill_name, dry_run)

    # Step 10: Switch back to main branch
    if not dry_run:
        run_git_command(['checkout', 'main'], repo_path)

    results['success'] = True
    return results


def main():
    parser = argparse.ArgumentParser(description='Publish skills to marketplace repositories')
    parser.add_argument('skill_path', type=Path,
                        help='Path to the skill directory to publish')
    parser.add_argument('--to', dest='marketplace',
                        help='Target marketplace name from config (prompts if not specified)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--no-pr', action='store_true',
                        help='Skip creating a pull request')
    parser.add_argument('--message', '-m',
                        help='Custom commit message')

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Resolve skill path
    skill_path = args.skill_path.resolve()

    # Validate source
    valid, message = validate_source_skill(skill_path)
    if not valid:
        print(f"ERROR: {message}")
        sys.exit(1)

    # Get marketplace (prompt if not specified)
    marketplace = args.marketplace
    if not marketplace:
        marketplace = prompt_for_marketplace(config)

    # Check if marketplace exists in config
    if marketplace not in config.get('marketplaces', {}):
        print(f"\nERROR: Marketplace '{marketplace}' not found in config.")
        print(f"Available marketplaces: {', '.join(config.get('marketplaces', {}).keys())}")
        sys.exit(1)

    # Check if repo is configured
    if not config['marketplaces'][marketplace].get('repo'):
        print(f"\nERROR: No repository configured for marketplace '{marketplace}'")
        print(f"Run 'scripts/init.py' to configure your marketplace repositories.")
        sys.exit(1)

    # Publish
    results = publish_skill(
        skill_path,
        marketplace,
        config,
        dry_run=args.dry_run,
        no_pr=args.no_pr,
        custom_message=args.message
    )

    # Summary
    print("\n" + "=" * 50)
    print("PUBLISH SUMMARY")
    print("=" * 50)
    print(f"Skill: {results['skill_name']}")
    print(f"Marketplace: {results['marketplace']}")
    print(f"Success: {'Yes' if results['success'] else 'No'}")
    if results['version']:
        print(f"Marketplace Version: {results['version']}")
    if results['pr_url']:
        print(f"PR URL: {results['pr_url']}")

    if results['success'] and not args.dry_run:
        print("\n" + "-" * 50)
        print("NEXT STEPS:")
        print("-" * 50)
        if results['pr_url']:
            print(f"1. Review and merge the PR: {results['pr_url']}")
        print(f"2. Once merged, users can install via:")
        print(f"   /plugin marketplace add <your-org>/skills-{marketplace}")
        print("-" * 50)

    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
