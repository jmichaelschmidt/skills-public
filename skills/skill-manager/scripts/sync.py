#!/usr/bin/env python3
"""
Skill Sync - Deploy skills across multiple AI platforms.

Usage:
    sync.py <skill-path> [options]
    sync.py --all [options]

Options:
    --to PLATFORMS       Target platforms (default: from config, or 'auto')
                         Can be: claude, codex, gemini, copilot, all, auto
    --dry-run           Preview changes without applying
    --force             Overwrite existing skills without prompting
    --mode MODE         Override sync mode: symlink or copy
    --all               Sync all skills from source platform to targets

Examples:
    sync.py ./my-skill                      # Sync using config settings
    sync.py ~/.claude/skills/my-skill       # Sync from Claude to configured targets
    sync.py --all                           # Sync all skills from source to targets
    sync.py ./my-skill --to codex,gemini    # Sync to specific platforms
    sync.py ./my-skill --to auto            # Auto-detect installed platforms
    sync.py ./my-skill --mode copy          # Force copy instead of symlink
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Default platform paths (used when no config exists)
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
    """Load configuration or return None if not configured."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return None


def get_platform_paths(config: dict = None) -> dict:
    """Get platform paths from config or defaults."""
    paths = {}
    if config and 'platforms' in config:
        for platform, pconfig in config['platforms'].items():
            paths[platform] = Path(pconfig.get('user_path', DEFAULT_PLATFORMS[platform]['user_path'])).expanduser()
    else:
        for platform, info in DEFAULT_PLATFORMS.items():
            paths[platform] = Path(info['user_path']).expanduser()
    return paths


def detect_platforms() -> list:
    """Detect which platforms are installed."""
    detected = []
    for platform, info in DEFAULT_PLATFORMS.items():
        path = Path(info['detect_path']).expanduser()
        if path.exists():
            detected.append(platform)
    return detected


def get_source_platform(config: dict = None) -> str:
    """Get the source platform from config."""
    if config and 'platforms' in config:
        for platform, pconfig in config['platforms'].items():
            if pconfig.get('is_source'):
                return platform
    return None


def get_target_platforms(config: dict = None) -> list:
    """Get enabled target platforms from config."""
    targets = []
    if config and 'platforms' in config:
        for platform, pconfig in config['platforms'].items():
            if pconfig.get('enabled') and not pconfig.get('is_source'):
                targets.append(platform)
    return targets


def get_sync_mode(config: dict = None) -> str:
    """Get sync mode from config."""
    if config:
        return config.get('sync_mode', 'symlink')
    return 'symlink'


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


def copy_skill(source: Path, target: Path, dry_run: bool = False) -> bool:
    """Copy a skill directory to target location."""
    if dry_run:
        print(f"  [DRY RUN] Would copy {source} -> {target}")
        return True

    try:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        print(f"  Copied {source.name} -> {target}")
        return True
    except Exception as e:
        print(f"  ERROR copying: {e}")
        return False


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


def sync_skill(skill_path: Path, platforms: list, platform_paths: dict,
               dry_run: bool = False, force: bool = False, mode: str = 'symlink') -> dict:
    """Sync a skill to specified platforms."""
    results = {'success': [], 'skipped': [], 'failed': []}

    skill_name = skill_path.name

    for platform in platforms:
        if platform not in platform_paths:
            print(f"Unknown platform: {platform}")
            results['failed'].append(platform)
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
            if not force and not dry_run:
                if not prompt_overwrite(target_skill):
                    print(f"  Skipped (not overwriting)")
                    results['skipped'].append(platform)
                    continue

        # Perform sync
        if mode == 'symlink':
            success = symlink_skill(skill_path, target_skill, dry_run)
        else:
            success = copy_skill(skill_path, target_skill, dry_run)

        if success:
            results['success'].append(platform)
        else:
            results['failed'].append(platform)

    return results


def get_all_skills(source_path: Path) -> list:
    """Get all valid skills from the source directory."""
    skills = []
    if not source_path.exists():
        return skills

    for item in source_path.iterdir():
        if item.is_dir() and (item / 'SKILL.md').exists():
            skills.append(item)

    return skills


def main():
    parser = argparse.ArgumentParser(description='Sync skills across AI platforms')
    parser.add_argument('skill_path', type=Path, nargs='?',
                        help='Path to the skill directory to sync')
    parser.add_argument('--to',
                        help='Target platforms: claude, codex, gemini, copilot, all, auto')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Overwrite existing skills without prompting')
    parser.add_argument('--mode',
                        help='Sync mode: symlink or copy (overrides config)')
    parser.add_argument('--all', action='store_true',
                        help='Sync all skills from source platform')

    args = parser.parse_args()

    # Load config
    config = load_config()
    platform_paths = get_platform_paths(config)

    # Determine sync mode
    if args.mode:
        sync_mode = args.mode
    else:
        sync_mode = get_sync_mode(config)

    # Determine target platforms
    if args.to:
        if args.to == 'all':
            platforms = list(DEFAULT_PLATFORMS.keys())
        elif args.to == 'auto':
            platforms = detect_platforms()
            print(f"Auto-detected platforms: {', '.join(platforms)}")
        else:
            platforms = [p.strip() for p in args.to.split(',')]
    else:
        # Use config
        platforms = get_target_platforms(config)
        if not platforms:
            print("No target platforms configured.")
            print("Run 'scripts/init.py' to set up platforms, or use --to to specify targets.")
            sys.exit(1)

    # Handle --all flag
    if args.all:
        source_platform = get_source_platform(config)
        if not source_platform:
            print("No source platform configured.")
            print("Run 'scripts/init.py' to set up your source platform.")
            sys.exit(1)

        source_path = platform_paths.get(source_platform)
        if not source_path or not source_path.exists():
            print(f"Source platform path does not exist: {source_path}")
            sys.exit(1)

        skills = get_all_skills(source_path)
        if not skills:
            print(f"No skills found in {source_path}")
            sys.exit(0)

        print(f"Syncing {len(skills)} skills from {DEFAULT_PLATFORMS[source_platform]['name']}")
        print(f"Targets: {', '.join(platforms)}")
        print(f"Mode: {sync_mode}")

        if args.dry_run:
            print("\n[DRY RUN MODE - No changes will be made]")

        # Remove source from targets
        platforms = [p for p in platforms if p != source_platform]

        all_results = {'success': 0, 'skipped': 0, 'failed': 0}
        for skill_path in skills:
            print(f"\n{'=' * 40}")
            print(f"Skill: {skill_path.name}")
            print('=' * 40)

            results = sync_skill(
                skill_path,
                platforms,
                platform_paths,
                dry_run=args.dry_run,
                force=args.force,
                mode=sync_mode
            )
            all_results['success'] += len(results['success'])
            all_results['skipped'] += len(results['skipped'])
            all_results['failed'] += len(results['failed'])

        print("\n" + "=" * 40)
        print("SUMMARY")
        print("=" * 40)
        print(f"Skills synced: {len(skills)}")
        print(f"Success: {all_results['success']}")
        print(f"Skipped: {all_results['skipped']}")
        print(f"Failed: {all_results['failed']}")

        sys.exit(1 if all_results['failed'] > 0 else 0)

    # Single skill sync
    if not args.skill_path:
        print("ERROR: Skill path required (or use --all to sync all skills)")
        parser.print_help()
        sys.exit(1)

    # Resolve skill path
    skill_path = args.skill_path.resolve()

    # Validate source
    valid, message = validate_source_skill(skill_path)
    if not valid:
        print(f"ERROR: {message}")
        sys.exit(1)

    # Determine source platform from skill path
    source_platform = None
    for platform, path in platform_paths.items():
        try:
            skill_path.relative_to(path)
            source_platform = platform
            break
        except ValueError:
            continue

    # Remove source platform from targets
    if source_platform and source_platform in platforms:
        platforms = [p for p in platforms if p != source_platform]

    if not platforms:
        print("No target platforms to sync to.")
        print("The skill is already in the only configured platform.")
        sys.exit(0)

    print(f"Syncing skill: {skill_path.name}")
    print(f"Source: {skill_path}")
    if source_platform:
        print(f"Source platform: {DEFAULT_PLATFORMS[source_platform]['name']}")
    print(f"Targets: {', '.join(platforms)}")
    print(f"Mode: {sync_mode}")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    # Perform sync
    results = sync_skill(
        skill_path,
        platforms,
        platform_paths,
        dry_run=args.dry_run,
        force=args.force,
        mode=sync_mode
    )

    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    if results['success']:
        print(f"Success: {', '.join(results['success'])}")
    if results['skipped']:
        print(f"Skipped: {', '.join(results['skipped'])}")
    if results['failed']:
        print(f"Failed: {', '.join(results['failed'])}")

    # IDE reload reminder
    if results['success']:
        print("\n" + "-" * 40)
        print("NOTE: Reload your IDE windows for changes to take effect.")
        print("VS Code: Cmd+Shift+P → 'Reload Window'")
        print("-" * 40)

    # Exit code
    if results['failed']:
        sys.exit(1)
    elif results['skipped'] and not results['success']:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
