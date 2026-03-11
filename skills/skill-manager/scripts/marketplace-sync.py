#!/usr/bin/env python3
"""
Marketplace Sync - Pull latest from configured marketplace repositories.

Usage:
    marketplace-sync.py [options]

Options:
    --marketplace NAME  Only sync a specific marketplace key from config
    --tier TIER         Backward-compatible alias for --marketplace
    --branch BRANCH     Override the branch to pull
    --auto-stash        Explicitly stash and restore local changes before pull
    --status            Show status only (no pull)

Examples:
    marketplace-sync.py
    marketplace-sync.py --marketplace team
    marketplace-sync.py --tier team
    marketplace-sync.py --branch master
    marketplace-sync.py --status
"""

import argparse
import subprocess
import sys
from pathlib import Path

from config_resolver import load_config_required




def load_config() -> dict:
    """Load configuration."""
    return load_config_required()


def parse_repo_name(repo_url: str) -> str:
    """Extract repo name from URL and strip optional .git suffix."""
    repo_name = repo_url.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def get_local_repo_path(config: dict, marketplace: str) -> Path:
    """Get local clone path for a marketplace key."""
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'].get(marketplace, {}).get('repo', '')
    if repo_url:
        return base_path / parse_repo_name(repo_url)
    return base_path / marketplace


def run_git(args: list, cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    """Run a git command."""
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"ERROR: git {' '.join(args)} failed in {cwd}")
        print(result.stderr.strip())
        sys.exit(1)
    return result


def detect_default_branch(repo_path: Path, remote: str = 'origin') -> str:
    """Detect default branch from remote HEAD."""
    symbolic = run_git(['symbolic-ref', f'refs/remotes/{remote}/HEAD'], repo_path)
    if symbolic.returncode == 0:
        ref = symbolic.stdout.strip()
        if ref:
            return ref.rsplit('/', 1)[-1]

    remote_show = run_git(['remote', 'show', remote], repo_path)
    if remote_show.returncode == 0:
        for line in remote_show.stdout.splitlines():
            line = line.strip()
            if line.startswith('HEAD branch:'):
                branch = line.split(':', 1)[1].strip()
                if branch and branch != '(unknown)':
                    return branch

    current = run_git(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path)
    if current.returncode == 0:
        branch = current.stdout.strip()
        if branch and branch != 'HEAD':
            return branch

    return 'main'


def has_uncommitted_changes(repo_path: Path) -> bool:
    """Return True when repository has local changes."""
    status = run_git(['status', '--porcelain'], repo_path)
    return bool(status.stdout.strip())


def get_repo_status(repo_path: Path, branch_override: str = None) -> dict:
    """Get status summary for a local repository."""
    status = {
        'exists': repo_path.exists(),
        'branch': None,
        'tracked_branch': None,
        'ahead': 0,
        'behind': 0,
        'dirty': False,
        'skills_count': 0,
    }

    if not status['exists']:
        return status

    current_branch = run_git(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path)
    if current_branch.returncode == 0:
        status['branch'] = current_branch.stdout.strip()

    run_git(['fetch', 'origin'], repo_path)

    tracked_branch = branch_override or detect_default_branch(repo_path)
    status['tracked_branch'] = tracked_branch

    revlist = run_git(['rev-list', '--left-right', '--count', f'HEAD...origin/{tracked_branch}'], repo_path)
    if revlist.returncode == 0:
        counts = revlist.stdout.strip().split()
        if len(counts) == 2:
            status['ahead'] = int(counts[0])
            status['behind'] = int(counts[1])

    status['dirty'] = has_uncommitted_changes(repo_path)

    skills_dir = repo_path / 'skills'
    if skills_dir.exists():
        status['skills_count'] = len([
            d for d in skills_dir.iterdir()
            if d.is_dir() and (d / 'SKILL.md').exists()
        ])

    return status


def sync_repo(repo_path: Path, marketplace: str, branch_override: str = None, auto_stash: bool = False) -> bool:
    """Pull latest changes for a repository."""
    print(f"\nSyncing {marketplace}...")

    if not repo_path.exists():
        print(f"  ERROR: Local repo not found at {repo_path}")
        print("  Run 'scripts/init.py' to set up repositories.")
        return False

    run_git(['fetch', 'origin'], repo_path)
    target_branch = branch_override or detect_default_branch(repo_path)

    stashed = False
    if has_uncommitted_changes(repo_path):
        if auto_stash:
            print("  Local changes detected; stashing due to --auto-stash")
            stash_result = run_git(['stash', 'push', '-u', '-m', 'skill-manager marketplace-sync --auto-stash'], repo_path)
            if stash_result.returncode != 0:
                print("  ERROR: Failed to stash changes")
                print(f"  {stash_result.stderr.strip()}")
                return False
            stashed = True
        else:
            print("  ERROR: Uncommitted changes detected")
            print("  Commit/stash changes or re-run with --auto-stash.")
            return False

    checkout = run_git(['checkout', target_branch], repo_path)
    if checkout.returncode != 0:
        print(f"  ERROR: Could not check out branch '{target_branch}'")
        print("  Use --branch to specify a branch explicitly.")
        return False

    pull = run_git(['pull', 'origin', target_branch], repo_path)
    if pull.returncode == 0:
        if 'Already up to date' in pull.stdout:
            print(f"  Already up to date ({target_branch})")
        else:
            print(f"  Updated successfully ({target_branch})")
            output = pull.stdout.strip()
            if output:
                print(f"  {output}")

        if stashed:
            print("  Restoring stashed changes...")
            stash_pop = run_git(['stash', 'pop'], repo_path)
            if stash_pop.returncode != 0:
                print("  WARNING: Could not auto-apply stashed changes.")
                print("  Run 'git stash list' and resolve manually.")
                print(f"  {stash_pop.stderr.strip()}")
        return True

    print("  ERROR: Pull failed")
    print(f"  {pull.stderr.strip()}")

    if stashed:
        print("  Local changes remain stashed. Use 'git stash list' to inspect.")

    return False


def show_status(config: dict, marketplaces: list, branch_override: str = None):
    """Show status of configured marketplace repos."""
    print("\n" + "=" * 70)
    print("MARKETPLACE STATUS")
    print("=" * 70)

    for marketplace in marketplaces:
        repo_url = config['marketplaces'][marketplace].get('repo', '')
        repo_path = get_local_repo_path(config, marketplace)
        status = get_repo_status(repo_path, branch_override)

        print(f"\n{marketplace.upper()}")
        print("-" * 40)
        print(f"  Remote: {repo_url or '(not configured)'}")
        print(f"  Local:  {repo_path}")

        if not status['exists']:
            print("  Status: NOT CLONED")
            continue

        status_parts = []
        if status['dirty']:
            status_parts.append('uncommitted changes')
        if status['behind'] > 0:
            status_parts.append(f"{status['behind']} behind")
        if status['ahead'] > 0:
            status_parts.append(f"{status['ahead']} ahead")

        if status_parts:
            print(f"  Status: {', '.join(status_parts)}")
        else:
            print("  Status: up to date")

        print(f"  Branch: {status['branch']}")
        print(f"  Tracking: origin/{status['tracked_branch']}")
        print(f"  Skills: {status['skills_count']}")

    print()


def resolve_target_marketplaces(config: dict, selected: str = None) -> list:
    """Resolve and validate requested marketplace keys."""
    configured = [
        name for name, info in config.get('marketplaces', {}).items()
        if info.get('repo')
    ]

    if selected:
        if selected not in config.get('marketplaces', {}):
            print(f"ERROR: Unknown marketplace '{selected}'")
            print(f"Configured marketplaces: {', '.join(config.get('marketplaces', {}).keys())}")
            sys.exit(1)
        if not config['marketplaces'][selected].get('repo'):
            print(f"ERROR: Marketplace '{selected}' has no repo configured")
            sys.exit(1)
        return [selected]

    return configured


def main():
    parser = argparse.ArgumentParser(description='Sync marketplace repositories')
    parser.add_argument('--marketplace', help='Only sync this marketplace key from config')
    parser.add_argument('--tier', help='Backward-compatible alias for --marketplace')
    parser.add_argument('--branch', help='Branch override (defaults to remote HEAD branch)')
    parser.add_argument('--auto-stash', action='store_true',
                        help='Explicitly stash and restore local changes before pull')
    parser.add_argument('--status', action='store_true',
                        help='Show status without pulling')

    args = parser.parse_args()

    if args.marketplace and args.tier and args.marketplace != args.tier:
        print("ERROR: --marketplace and --tier must match when both are provided")
        sys.exit(1)

    selected_marketplace = args.marketplace or args.tier

    config = load_config()
    marketplaces = resolve_target_marketplaces(config, selected_marketplace)

    if not marketplaces:
        print("No marketplace repositories configured.")
        print("Run 'scripts/init.py' to set up your marketplaces.")
        sys.exit(1)

    if args.status:
        show_status(config, marketplaces, args.branch)
        return

    print("=" * 50)
    print("MARKETPLACE SYNC")
    print("=" * 50)

    results = {}
    for marketplace in marketplaces:
        repo_path = get_local_repo_path(config, marketplace)
        results[marketplace] = sync_repo(
            repo_path,
            marketplace,
            branch_override=args.branch,
            auto_stash=args.auto_stash,
        )

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    success = [name for name, ok in results.items() if ok]
    failed = [name for name, ok in results.items() if not ok]

    if success:
        print(f"Synced: {', '.join(success)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")

    show_status(config, marketplaces, args.branch)
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
