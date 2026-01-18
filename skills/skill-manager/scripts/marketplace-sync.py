#!/usr/bin/env python3
"""
Marketplace Sync - Pull latest from all configured marketplace repositories.

Usage:
    marketplace-sync.py [options]

Options:
    --tier TIER         Only sync specific tier: private, team, public
    --status            Just show status, don't pull

Examples:
    marketplace-sync.py                # Sync all tiers
    marketplace-sync.py --tier team    # Only sync team marketplace
    marketplace-sync.py --status       # Show status without pulling
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'


def load_config() -> dict:
    """Load marketplace configuration."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        print("Run 'scripts/init.py' to set up your marketplace configuration.")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_local_repo_path(config: dict, tier: str) -> Path:
    """Get the local clone path for a marketplace repo.

    Derives the folder name from the repo URL (e.g., 'skills-team' from
    'https://github.com/org/skills-team').
    """
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'][tier].get('repo', '')
    if repo_url:
        # Extract repo name from URL (last part of path, minus .git if present)
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return base_path / repo_name
    # Fallback to default naming if no URL configured
    return base_path / f"skills-{tier}"


def get_repo_status(repo_path: Path) -> dict:
    """Get the status of a local repository."""
    status = {
        'exists': repo_path.exists(),
        'branch': None,
        'ahead': 0,
        'behind': 0,
        'dirty': False,
        'skills_count': 0
    }

    if not status['exists']:
        return status

    # Get current branch
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        status['branch'] = result.stdout.strip()

    # Fetch to get accurate ahead/behind
    subprocess.run(
        ['git', 'fetch', 'origin'],
        cwd=repo_path,
        capture_output=True
    )

    # Get ahead/behind counts
    result = subprocess.run(
        ['git', 'rev-list', '--left-right', '--count', f'{status["branch"]}...origin/{status["branch"]}'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        parts = result.stdout.strip().split()
        if len(parts) == 2:
            status['ahead'] = int(parts[0])
            status['behind'] = int(parts[1])

    # Check for uncommitted changes
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    status['dirty'] = bool(result.stdout.strip())

    # Count skills
    skills_dir = repo_path / 'skills'
    if skills_dir.exists():
        status['skills_count'] = len([
            d for d in skills_dir.iterdir()
            if d.is_dir() and (d / 'SKILL.md').exists()
        ])

    return status


def sync_repo(repo_path: Path, tier: str) -> bool:
    """Pull latest changes for a repository."""
    print(f"\nSyncing {tier}...")

    if not repo_path.exists():
        print(f"  ERROR: Local repo not found at {repo_path}")
        print(f"  Run 'scripts/init.py' to set up repositories.")
        return False

    # Check for uncommitted changes
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        print(f"  WARNING: Uncommitted changes in {repo_path}")
        print(f"  Stashing changes before pull...")
        subprocess.run(['git', 'stash'], cwd=repo_path)

    # Ensure on main branch
    subprocess.run(
        ['git', 'checkout', 'main'],
        cwd=repo_path,
        capture_output=True
    )

    # Pull latest
    result = subprocess.run(
        ['git', 'pull', 'origin', 'main'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        if 'Already up to date' in result.stdout:
            print(f"  Already up to date")
        else:
            print(f"  Updated successfully")
            print(f"  {result.stdout.strip()}")
        return True
    else:
        print(f"  ERROR: Pull failed")
        print(f"  {result.stderr}")
        return False


def show_status(config: dict, tiers: list):
    """Show status of all marketplace repos."""
    print("\n" + "=" * 70)
    print("MARKETPLACE STATUS")
    print("=" * 70)

    for tier in tiers:
        repo_url = config['marketplaces'][tier].get('repo', '')
        repo_path = get_local_repo_path(config, tier)
        status = get_repo_status(repo_path)

        print(f"\n{tier.upper()}")
        print("-" * 40)
        print(f"  Remote: {repo_url or '(not configured)'}")
        print(f"  Local:  {repo_path}")

        if not status['exists']:
            print(f"  Status: NOT CLONED")
            continue

        status_parts = []
        if status['dirty']:
            status_parts.append("uncommitted changes")
        if status['behind'] > 0:
            status_parts.append(f"{status['behind']} behind")
        if status['ahead'] > 0:
            status_parts.append(f"{status['ahead']} ahead")

        if status_parts:
            print(f"  Status: {', '.join(status_parts)}")
        else:
            print(f"  Status: up to date")

        print(f"  Branch: {status['branch']}")
        print(f"  Skills: {status['skills_count']}")

    print()


def main():
    parser = argparse.ArgumentParser(description='Sync marketplace repositories')
    parser.add_argument('--tier', choices=['private', 'team', 'public'],
                        help='Only sync specific tier')
    parser.add_argument('--status', action='store_true',
                        help='Show status without pulling')

    args = parser.parse_args()

    config = load_config()

    # Determine which tiers to process
    if args.tier:
        tiers = [args.tier]
    else:
        tiers = ['private', 'team', 'public']

    # Filter to only configured tiers
    tiers = [t for t in tiers if config['marketplaces'][t].get('repo')]

    if not tiers:
        print("No marketplace repositories configured.")
        print("Run 'scripts/init.py' to set up your marketplaces.")
        sys.exit(1)

    if args.status:
        show_status(config, tiers)
        return

    # Sync each tier
    print("=" * 50)
    print("MARKETPLACE SYNC")
    print("=" * 50)

    results = {}
    for tier in tiers:
        repo_path = get_local_repo_path(config, tier)
        results[tier] = sync_repo(repo_path, tier)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    success = [t for t, ok in results.items() if ok]
    failed = [t for t, ok in results.items() if not ok]

    if success:
        print(f"Synced: {', '.join(success)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")

    # Show current status
    show_status(config, tiers)

    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
