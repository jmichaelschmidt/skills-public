#!/usr/bin/env python3
"""
Install or refresh published skills from local marketplace clones into runtime paths.

Usage:
    install-from-marketplace.py --marketplace <name> --skill <name> [options]
    install-from-marketplace.py --marketplace <name> --all [options]

Options:
    --marketplace NAME    Marketplace key from config
    --skill NAME          Skill to install or refresh
    --all                 Refresh all published skills from the selected marketplace
    --source-dir DIR      Published skill directory: skills or skills-in-development
    --dry-run             Preview changes without applying
    --no-codex            Skip Codex symlink verification/refresh
"""

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_resolver import load_config_required


DEFAULT_PLATFORMS = {
    'claude': {
        'name': 'Claude Code',
        'user_path': '~/.claude/skills',
    },
    'codex': {
        'name': 'OpenAI Codex',
        'user_path': '~/.codex/skills',
    },
}


def load_config() -> dict:
    """Load required config."""
    return load_config_required()


def get_platform_paths(config: dict) -> dict:
    """Resolve platform paths from config with defaults."""
    paths = {}
    platforms = config.get('platforms', {})
    for platform, defaults in DEFAULT_PLATFORMS.items():
        user_path = platforms.get(platform, {}).get('user_path', defaults['user_path'])
        paths[platform] = Path(user_path).expanduser()
    return paths


def get_runtime_settings(config: dict) -> tuple[str, bool]:
    """Resolve canonical runtime settings with backward-compatible defaults."""
    runtime = config.get('runtime', {})
    primary_platform = runtime.get('primary_platform', 'claude')
    codex_mirrors_claude = runtime.get('codex_mirrors_claude', True)
    return primary_platform, codex_mirrors_claude


def get_local_repo_path(config: dict, marketplace: str) -> Path:
    """Get the local clone path for a marketplace repo."""
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'].get(marketplace, {}).get('repo', '')
    if repo_url:
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return base_path / repo_name
    return base_path / marketplace


def discover_marketplace_skills(config: dict, marketplace: str, source_dir: str) -> list[dict]:
    """Discover published skills in the configured marketplace clone."""
    repo_path = get_local_repo_path(config, marketplace)
    skills_dir = repo_path / source_dir
    discovered = []

    if not skills_dir.exists():
        return discovered

    for item in sorted(skills_dir.iterdir()):
        if item.is_dir() and (item / 'SKILL.md').exists():
            discovered.append({
                'name': item.name,
                'path': item,
                'marketplace': marketplace,
            })

    return discovered


def replace_install(source: Path, target: Path, dry_run: bool = False):
    """Replace an installed skill directory with a fresh copy."""
    if dry_run:
        print(f"  [DRY RUN] Would replace {target} from {source}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)

    shutil.copytree(source, target)
    print(f"  Installed runtime copy: {target}")


def ensure_symlink(link_path: Path, target_path: Path, dry_run: bool = False):
    """Ensure a symlink points at the intended target."""
    if dry_run:
        print(f"  [DRY RUN] Would symlink {link_path} -> {target_path}")
        return

    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        link_path.unlink()
    elif link_path.exists():
        shutil.rmtree(link_path)

    link_path.symlink_to(target_path.resolve())
    print(f"  Updated symlink: {link_path} -> {target_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Install or refresh published skills from marketplace clones into runtime paths'
    )
    parser.add_argument('--marketplace', required=True,
                        help='Marketplace key from config')
    parser.add_argument('--skill',
                        help='Skill to install or refresh')
    parser.add_argument('--all', action='store_true',
                        help='Refresh all published skills from the selected marketplace')
    parser.add_argument('--source-dir', default='skills', choices=['skills', 'skills-in-development'],
                        help='Published skill directory inside the marketplace clone')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--no-codex', action='store_true',
                        help='Skip Codex symlink verification and refresh')
    args = parser.parse_args()

    if not args.skill and not args.all:
        parser.error('pass --skill NAME or --all')

    config = load_config()
    if args.marketplace not in config.get('marketplaces', {}):
        print(f"ERROR: Marketplace '{args.marketplace}' not found in config.")
        sys.exit(1)

    platform_paths = get_platform_paths(config)
    primary_platform, codex_mirrors_claude = get_runtime_settings(config)
    primary_runtime_dir = platform_paths.get(primary_platform, platform_paths['claude'])

    skills = discover_marketplace_skills(config, args.marketplace, args.source_dir)
    if not skills:
        print(f"ERROR: No skills found in marketplace '{args.marketplace}' under '{args.source_dir}'.")
        sys.exit(1)

    if args.skill:
        skills = [skill for skill in skills if skill['name'] == args.skill]
        if not skills:
            print(f"ERROR: Skill '{args.skill}' not found in marketplace '{args.marketplace}'.")
            sys.exit(1)

    print("=" * 60)
    print("RUNTIME INSTALL")
    print("=" * 60)
    print(f"Marketplace: {args.marketplace}")
    print(f"Source dir: {args.source_dir}")
    print(f"Primary runtime: {primary_platform} -> {primary_runtime_dir}")
    print(f"Codex mirror: {'disabled' if args.no_codex else codex_mirrors_claude}")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    for skill in skills:
        skill_name = skill['name']
        source_path = skill['path']
        primary_skill_path = primary_runtime_dir / skill_name

        print(f"\n{'=' * 40}")
        print(f"Skill: {skill_name}")
        print('=' * 40)
        print(f"  Source: {source_path}")

        replace_install(source_path, primary_skill_path, dry_run=args.dry_run)

        if not args.no_codex and codex_mirrors_claude:
            codex_skill_path = platform_paths['codex'] / skill_name
            ensure_symlink(codex_skill_path, primary_skill_path, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Skills processed: {len(skills)}")
    print("Runtime installs are now anchored in the configured primary runtime path.")
    print("Reload your IDE window if the assistant does not pick up the refreshed skill immediately.")


if __name__ == '__main__':
    main()
