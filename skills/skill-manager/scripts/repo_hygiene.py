#!/usr/bin/env python3
"""Shared git hygiene helpers for skill-manager marketplace repos."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    """Run a git command."""
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


def detect_default_branch(repo_path: Path, remote: str = 'origin') -> str:
    """Detect the repository default branch from origin/HEAD."""
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
    """Return True when git status has tracked or untracked changes."""
    status = run_git(['status', '--porcelain'], repo_path)
    return bool(status.stdout.strip())


def get_current_branch(repo_path: Path) -> str | None:
    """Return the currently checked out branch, if any."""
    current_branch = run_git(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path)
    if current_branch.returncode != 0:
        return None

    branch = current_branch.stdout.strip()
    return branch or None


def list_local_branches(repo_path: Path) -> list[str]:
    """Return all local branch names."""
    branches = run_git(['branch', '--format=%(refname:short)'], repo_path)
    if branches.returncode != 0:
        return []

    return [line.strip() for line in branches.stdout.splitlines() if line.strip()]


def get_branch_divergence(repo_path: Path, tracked_branch: str) -> tuple[int, int]:
    """Return (ahead, behind) counts for HEAD against origin/tracked_branch."""
    revlist = run_git(['rev-list', '--left-right', '--count', f'HEAD...origin/{tracked_branch}'], repo_path)
    if revlist.returncode != 0:
        return (0, 0)

    counts = revlist.stdout.strip().split()
    if len(counts) != 2:
        return (0, 0)

    return (int(counts[0]), int(counts[1]))


def get_extra_local_branches(repo_path: Path, keep_branches: set[str] | None = None) -> list[str]:
    """Return local branches outside the keep set."""
    keep = keep_branches or set()
    return [branch for branch in list_local_branches(repo_path) if branch not in keep]


def get_merged_local_branches(repo_path: Path, base_branch: str, keep_branches: set[str] | None = None) -> list[str]:
    """Return local branches already merged into the base branch."""
    keep = keep_branches or set()
    merged = run_git(['branch', '--format=%(refname:short)', '--merged', base_branch], repo_path)
    if merged.returncode != 0:
        return []

    return [
        branch.strip()
        for branch in merged.stdout.splitlines()
        if branch.strip() and branch.strip() not in keep
    ]


def prune_merged_branches(repo_path: Path, base_branch: str, keep_branches: set[str] | None = None) -> list[str]:
    """Delete merged local branches and return the branches that were pruned."""
    keep = keep_branches or set()
    pruned: list[str] = []

    for branch in get_merged_local_branches(repo_path, base_branch, keep):
        delete_result = run_git(['branch', '-d', branch], repo_path)
        if delete_result.returncode == 0:
            pruned.append(branch)

    return pruned


def get_repo_status(repo_path: Path, branch_override: str | None = None, fetch: bool = True) -> dict:
    """Return a git hygiene summary for a local marketplace repository."""
    status = {
        'exists': repo_path.exists(),
        'branch': None,
        'tracked_branch': None,
        'ahead': 0,
        'behind': 0,
        'dirty': False,
        'skills_count': 0,
        'extra_local_branches': [],
        'merged_local_branches': [],
        'aligned': False,
        'issues': [],
    }

    if not status['exists']:
        return status

    if fetch:
        run_git(['fetch', 'origin'], repo_path)

    status['branch'] = get_current_branch(repo_path)
    status['tracked_branch'] = branch_override or detect_default_branch(repo_path)
    status['dirty'] = has_uncommitted_changes(repo_path)
    status['ahead'], status['behind'] = get_branch_divergence(repo_path, status['tracked_branch'])

    keep_branches = {status['tracked_branch']}
    if status['branch'] and status['branch'] != 'HEAD':
        keep_branches.add(status['branch'])

    status['extra_local_branches'] = get_extra_local_branches(repo_path, keep_branches)
    status['merged_local_branches'] = get_merged_local_branches(repo_path, status['tracked_branch'], keep_branches)

    skills_dir = repo_path / 'skills'
    if skills_dir.exists():
        status['skills_count'] = len([
            entry for entry in skills_dir.iterdir()
            if entry.is_dir() and (entry / 'SKILL.md').exists()
        ])

    if status['branch'] and status['branch'] != status['tracked_branch']:
        status['issues'].append(
            f"checked out on '{status['branch']}' instead of '{status['tracked_branch']}'"
        )
    if status['dirty']:
        status['issues'].append('uncommitted changes present')
    if status['behind'] > 0:
        status['issues'].append(f"behind origin/{status['tracked_branch']} by {status['behind']}")
    if status['ahead'] > 0:
        status['issues'].append(f"ahead of origin/{status['tracked_branch']} by {status['ahead']}")
    if status['extra_local_branches']:
        status['issues'].append(
            f"extra local branches: {', '.join(status['extra_local_branches'])}"
        )

    status['aligned'] = not status['issues']
    return status
