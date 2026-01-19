#!/usr/bin/env python3
"""
Marketplace Distribute - Make marketplace skills available to other AI platforms via symlinks.

This script creates symlinks in other AI platforms' skill directories (Codex, Gemini, Copilot)
pointing to skills in your local marketplace repository clones. Since Claude Code already has
access to marketplace skills through its plugin system, it is skipped by default.

Usage:
    marketplace-distribute.py [options]
    marketplace-distribute.py --marketplace <name> [options]
    marketplace-distribute.py --skill <name> [options]

Options:
    --marketplace NAME   Only distribute skills from specific marketplace
    --skill NAME         Only distribute a specific skill (by name)
    --to PLATFORMS       Target platforms: codex, gemini, copilot, all (default: from config)
    --include-claude     Also create symlinks for Claude (normally skipped)
    --dry-run           Preview changes without applying
    --force             Overwrite existing skills without prompting
    --list              List available marketplace skills and exit
    --status            Show current distribution status

Examples:
    marketplace-distribute.py                           # Distribute all marketplace skills
    marketplace-distribute.py --marketplace team        # Only from team marketplace
    marketplace-distribute.py --skill my-cool-skill     # Only distribute one skill
    marketplace-distribute.py --to codex,gemini         # Only to specific platforms
    marketplace-distribute.py --dry-run                 # Preview what would happen
    marketplace-distribute.py --list                    # Show available skills
    marketplace-distribute.py --status                  # Show what's already distributed
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

DEFAULT_PLATFORMS = {
    'claude': {
        'name': 'Claude Code',
        'user_path': '~/.claude/skills',
        'detect_path': '~/.claude'
    },
    'codex': {
        'name': 'OpenAI Codex',
        'user_path': '~/.codex/skills',
        'detect_path': '~/.codex'
    },
    'gemini': {
        'name': 'Gemini CLI',
        'user_path': '~/.gemini/skills',
        'detect_path': '~/.gemini'
    },
    'copilot': {
        'name': 'GitHub Copilot',
        'user_path': '~/.copilot/skills',
        'detect_path': '~/.copilot'
    }
}


def load_config() -> dict:
    """Load marketplace configuration."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        print("Run 'scripts/init.py' to set up your marketplace configuration.")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_platform_paths(config: dict) -> dict:
    """Get platform paths from config or defaults."""
    paths = {}
    if config and 'platforms' in config:
        for platform, pconfig in config['platforms'].items():
            paths[platform] = Path(pconfig.get('user_path', DEFAULT_PLATFORMS[platform]['user_path'])).expanduser()
    else:
        for platform, info in DEFAULT_PLATFORMS.items():
            paths[platform] = Path(info['user_path']).expanduser()
    return paths


def get_target_platforms(config: dict, include_claude: bool = False) -> list:
    """Get enabled target platforms from config, excluding Claude by default."""
    targets = []
    if config and 'platforms' in config:
        for platform, pconfig in config['platforms'].items():
            if pconfig.get('enabled'):
                # Skip Claude unless explicitly included (Claude has native marketplace access)
                if platform == 'claude' and not include_claude:
                    continue
                targets.append(platform)
    return targets


def get_local_repo_path(config: dict, marketplace: str) -> Path:
    """Get the local clone path for a marketplace repo."""
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'].get(marketplace, {}).get('repo', '')
    if repo_url:
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return base_path / repo_name
    return base_path / f"skills-{marketplace}"


def discover_marketplace_skills(config: dict, marketplace_filter: str = None) -> list:
    """Discover all skills in configured marketplace local clones."""
    skills = []

    marketplaces = config.get('marketplaces', {})

    for marketplace_name, marketplace_config in marketplaces.items():
        # Skip if filtering to specific marketplace
        if marketplace_filter and marketplace_name != marketplace_filter:
            continue

        repo_path = get_local_repo_path(config, marketplace_name)
        skills_dir = repo_path / 'skills'

        if not skills_dir.exists():
            continue

        for item in skills_dir.iterdir():
            if item.is_dir() and (item / 'SKILL.md').exists():
                # Parse skill metadata
                skill_info = {
                    'name': item.name,
                    'path': item,
                    'marketplace': marketplace_name,
                    'description': ''
                }

                # Try to extract description from SKILL.md frontmatter
                skill_md = item / 'SKILL.md'
                try:
                    content = skill_md.read_text()
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            for line in parts[1].split('\n'):
                                if line.startswith('description:'):
                                    skill_info['description'] = line.split(':', 1)[1].strip().strip('"\'')
                                    break
                except Exception:
                    pass

                skills.append(skill_info)

    return skills


def symlink_skill(source: Path, target: Path, dry_run: bool = False) -> bool:
    """Create a symlink to the skill directory."""
    if dry_run:
        print(f"  [DRY RUN] Would symlink {target} -> {source}")
        return True

    try:
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            else:
                shutil.rmtree(target)
        target.symlink_to(source.resolve())
        print(f"  Symlinked {target.name} -> {source}")
        return True
    except Exception as e:
        print(f"  ERROR creating symlink: {e}")
        return False


def prompt_overwrite(target: Path) -> bool:
    """Ask user whether to overwrite existing skill."""
    response = input(f"  Skill already exists at {target}. Overwrite? [y/N]: ")
    return response.lower() in ('y', 'yes')


def get_distribution_status(config: dict, platform_paths: dict, include_claude: bool = False) -> dict:
    """Check which marketplace skills are already distributed to which platforms."""
    status = {}
    marketplace_skills = discover_marketplace_skills(config)

    for skill in marketplace_skills:
        skill_name = skill['name']
        skill_source = skill['path'].resolve()
        status[skill_name] = {
            'marketplace': skill['marketplace'],
            'source': str(skill_source),
            'platforms': {}
        }

        for platform, path in platform_paths.items():
            if platform == 'claude' and not include_claude:
                continue

            target = path / skill_name
            if target.is_symlink():
                link_target = target.resolve()
                if link_target == skill_source:
                    status[skill_name]['platforms'][platform] = 'linked'
                else:
                    status[skill_name]['platforms'][platform] = f'linked-other ({link_target})'
            elif target.exists():
                status[skill_name]['platforms'][platform] = 'exists (not symlink)'
            else:
                status[skill_name]['platforms'][platform] = 'not distributed'

    return status


def show_list(config: dict):
    """List all available marketplace skills."""
    skills = discover_marketplace_skills(config)

    if not skills:
        print("No marketplace skills found.")
        print("Make sure your marketplace repos are cloned locally.")
        return

    print("\n" + "=" * 70)
    print("MARKETPLACE SKILLS")
    print("=" * 70)

    # Group by marketplace
    by_marketplace = {}
    for skill in skills:
        mp = skill['marketplace']
        if mp not in by_marketplace:
            by_marketplace[mp] = []
        by_marketplace[mp].append(skill)

    for marketplace, mp_skills in sorted(by_marketplace.items()):
        print(f"\n{marketplace.upper()} ({len(mp_skills)} skills)")
        print("-" * 40)
        for skill in sorted(mp_skills, key=lambda s: s['name']):
            desc = skill['description'][:50] + '...' if len(skill['description']) > 50 else skill['description']
            print(f"  {skill['name']:<30} {desc}")

    print()


def show_status(config: dict, platform_paths: dict, include_claude: bool = False):
    """Show distribution status of all marketplace skills."""
    targets = get_target_platforms(config, include_claude)
    status = get_distribution_status(config, platform_paths, include_claude)

    if not status:
        print("No marketplace skills found.")
        return

    print("\n" + "=" * 70)
    print("DISTRIBUTION STATUS")
    print("=" * 70)

    # Header
    platform_names = [DEFAULT_PLATFORMS[p]['name'][:10] for p in targets]
    header = f"{'Skill':<25} {'Marketplace':<12} " + " ".join(f"{n:<12}" for n in platform_names)
    print(f"\n{header}")
    print("-" * len(header))

    for skill_name, info in sorted(status.items()):
        row = f"{skill_name:<25} {info['marketplace']:<12} "
        for platform in targets:
            state = info['platforms'].get(platform, 'n/a')
            if state == 'linked':
                indicator = 'Y'
            elif state == 'not distributed':
                indicator = '-'
            else:
                indicator = '?'
            row += f"{indicator:<12} "
        print(row)

    print()
    print("Legend: Y = symlinked, - = not distributed, ? = other state")
    print()


def distribute_skills(config: dict, platform_paths: dict, skills: list, platforms: list,
                      dry_run: bool = False, force: bool = False) -> dict:
    """Distribute skills to target platforms."""
    results = {'success': 0, 'skipped': 0, 'failed': 0}

    for skill in skills:
        skill_name = skill['name']
        skill_path = skill['path']
        marketplace = skill['marketplace']

        print(f"\n{'=' * 50}")
        print(f"Skill: {skill_name} (from {marketplace})")
        print('=' * 50)

        for platform in platforms:
            if platform not in platform_paths:
                print(f"  {platform}: Unknown platform")
                results['failed'] += 1
                continue

            target_dir = platform_paths[platform]
            target_skill = target_dir / skill_name

            platform_name = DEFAULT_PLATFORMS.get(platform, {}).get('name', platform.upper())
            print(f"\n{platform_name}:")

            # Ensure parent directory exists
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)

            # Check if skill already exists
            if target_skill.exists() or target_skill.is_symlink():
                # Check if it's already a symlink to the same source
                if target_skill.is_symlink():
                    current_target = target_skill.resolve()
                    if current_target == skill_path.resolve():
                        print(f"  Already linked correctly")
                        results['skipped'] += 1
                        continue

                if not force and not dry_run:
                    if not prompt_overwrite(target_skill):
                        print(f"  Skipped (not overwriting)")
                        results['skipped'] += 1
                        continue

            # Create symlink
            success = symlink_skill(skill_path, target_skill, dry_run)

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Distribute marketplace skills to other AI platforms via symlinks'
    )
    parser.add_argument('--marketplace', '-m',
                        help='Only distribute from specific marketplace')
    parser.add_argument('--skill', '-s',
                        help='Only distribute a specific skill by name')
    parser.add_argument('--to',
                        help='Target platforms: codex, gemini, copilot, all')
    parser.add_argument('--include-claude', action='store_true',
                        help='Also create symlinks for Claude (normally skipped)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Overwrite existing skills without prompting')
    parser.add_argument('--list', action='store_true',
                        help='List available marketplace skills')
    parser.add_argument('--status', action='store_true',
                        help='Show current distribution status')

    args = parser.parse_args()

    config = load_config()
    platform_paths = get_platform_paths(config)

    # Handle --list
    if args.list:
        show_list(config)
        return

    # Handle --status
    if args.status:
        show_status(config, platform_paths, args.include_claude)
        return

    # Discover skills
    skills = discover_marketplace_skills(config, args.marketplace)

    if not skills:
        print("No marketplace skills found.")
        if args.marketplace:
            print(f"Check that the '{args.marketplace}' marketplace is configured and cloned.")
        else:
            print("Make sure your marketplace repos are cloned locally.")
        sys.exit(1)

    # Filter to specific skill if requested
    if args.skill:
        skills = [s for s in skills if s['name'] == args.skill]
        if not skills:
            print(f"Skill '{args.skill}' not found in any marketplace.")
            print("Use --list to see available skills.")
            sys.exit(1)

    # Determine target platforms
    if args.to:
        if args.to == 'all':
            platforms = [p for p in DEFAULT_PLATFORMS.keys() if p != 'claude' or args.include_claude]
        else:
            platforms = [p.strip() for p in args.to.split(',')]
            # Remove claude unless explicitly included
            if 'claude' in platforms and not args.include_claude:
                platforms.remove('claude')
                print("Note: Skipping Claude (use --include-claude to include it)")
    else:
        platforms = get_target_platforms(config, args.include_claude)

    if not platforms:
        print("No target platforms configured or specified.")
        print("Use --to to specify platforms, or configure them with 'scripts/init.py'")
        sys.exit(1)

    # Show plan
    print("=" * 60)
    print("MARKETPLACE DISTRIBUTION")
    print("=" * 60)
    print(f"\nSkills to distribute: {len(skills)}")
    print(f"Target platforms: {', '.join(platforms)}")

    if args.marketplace:
        print(f"From marketplace: {args.marketplace}")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    # Perform distribution
    results = distribute_skills(
        config,
        platform_paths,
        skills,
        platforms,
        dry_run=args.dry_run,
        force=args.force
    )

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Symlinks created: {results['success']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Failed: {results['failed']}")

    # IDE reload reminder
    if results['success'] > 0 and not args.dry_run:
        print("\n" + "-" * 60)
        print("NOTE: Reload your IDE windows for changes to take effect.")
        print("VS Code: Cmd+Shift+P -> 'Reload Window'")
        print("-" * 60)

    sys.exit(1 if results['failed'] > 0 else 0)


if __name__ == '__main__':
    main()
