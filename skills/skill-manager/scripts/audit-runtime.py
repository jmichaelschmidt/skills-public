#!/usr/bin/env python3
"""
Audit repo source, marketplace artifact, and runtime install drift for one skill.

Usage:
    audit-runtime.py <skill-name> [--marketplace <name>] [--source <path>] [--format text|json]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_resolver import load_config_required


DEFAULT_PLATFORMS = {
    'claude': {'user_path': '~/.claude/skills'},
    'codex': {'user_path': '~/.codex/skills'},
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


def hash_file(path: Path) -> str:
    """Hash a file for tree comparison."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def snapshot_tree(path: Path) -> dict:
    """Snapshot all files in a skill tree."""
    if not path.exists():
        return {}

    snapshot = {}
    for item in path.rglob('*'):
        if item.is_file():
            snapshot[str(item.relative_to(path))] = hash_file(item)
    return snapshot


def compare_skill_trees(expected: Path, actual: Path) -> dict:
    """Compare two skill directories."""
    if not expected.exists():
        return {'status': 'missing-expected'}
    if not actual.exists():
        return {'status': 'missing-actual'}

    expected_files = snapshot_tree(expected)
    actual_files = snapshot_tree(actual)

    if expected_files == actual_files:
        return {'status': 'match'}

    missing = sorted(set(expected_files) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected_files))
    modified = sorted(
        path for path in set(expected_files) & set(actual_files)
        if expected_files[path] != actual_files[path]
    )
    return {
        'status': 'drift',
        'missing': missing,
        'extra': extra,
        'modified': modified,
    }


def classify_codex_runtime(primary_skill: Path, codex_skill: Path) -> dict:
    """Classify Codex runtime state relative to the primary runtime copy."""
    if not codex_skill.exists() and not codex_skill.is_symlink():
        return {'status': 'missing'}
    if codex_skill.is_symlink() and codex_skill.resolve() == primary_skill.resolve():
        return {'status': 'mirrored', 'target': str(codex_skill.resolve())}
    if codex_skill.is_symlink():
        return {'status': 'wrong-target', 'target': str(codex_skill.resolve())}
    return {'status': 'copied', 'comparison': compare_skill_trees(primary_skill, codex_skill)}


def build_report(skill_name: str, config: dict, marketplace: str = None, source: Path = None) -> dict:
    """Build a runtime report for one skill."""
    platform_paths = get_platform_paths(config)
    primary_platform, codex_mirrors_claude = get_runtime_settings(config)
    primary_runtime = platform_paths.get(primary_platform, platform_paths['claude']) / skill_name
    codex_runtime = platform_paths['codex'] / skill_name

    report = {
        'skill': skill_name,
        'runtime': {
            'primary_platform': primary_platform,
            'primary_path': str(primary_runtime),
            'primary_exists': primary_runtime.exists(),
            'codex_path': str(codex_runtime),
            'codex_expected_to_mirror': codex_mirrors_claude,
            'codex': classify_codex_runtime(primary_runtime, codex_runtime),
        },
    }

    if source:
        report['source'] = {
            'path': str(source),
            'exists': source.exists(),
        }

    if marketplace:
        marketplace_path = get_local_repo_path(config, marketplace) / 'skills' / skill_name
        report['marketplace'] = {
            'name': marketplace,
            'path': str(marketplace_path),
            'exists': marketplace_path.exists(),
            'vs_runtime': compare_skill_trees(marketplace_path, primary_runtime),
        }
        if source:
            report['source']['vs_marketplace'] = compare_skill_trees(source, marketplace_path)

    return report


def format_text_report(report: dict) -> str:
    """Render a human-readable runtime report."""
    lines = []
    lines.append("=" * 60)
    lines.append("RUNTIME AUDIT")
    lines.append("=" * 60)
    lines.append(f"Skill: {report['skill']}")

    if 'source' in report:
        lines.append(f"Repo source: {report['source']['path']}")
        if report['source'].get('vs_marketplace'):
            lines.append(f"  Source vs marketplace: {report['source']['vs_marketplace']['status']}")

    if 'marketplace' in report:
        lines.append(f"Marketplace artifact ({report['marketplace']['name']}): {report['marketplace']['path']}")
        lines.append(f"  Marketplace vs runtime: {report['marketplace']['vs_runtime']['status']}")

    runtime = report['runtime']
    lines.append(f"Primary runtime ({runtime['primary_platform']}): {runtime['primary_path']}")
    lines.append(f"  Exists: {'yes' if runtime['primary_exists'] else 'no'}")
    lines.append(f"Codex path: {runtime['codex_path']}")
    lines.append(f"  Codex state: {runtime['codex']['status']}")
    if runtime['codex'].get('target'):
        lines.append(f"  Codex target: {runtime['codex']['target']}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Audit repo source, marketplace artifact, and runtime drift')
    parser.add_argument('skill_name', help='Skill name to audit')
    parser.add_argument('--marketplace', help='Marketplace key from config')
    parser.add_argument('--source', type=Path, help='Repo source skill path for repo vs marketplace comparison')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    args = parser.parse_args()

    config = load_config()
    source = args.source.expanduser().resolve() if args.source else None
    report = build_report(args.skill_name, config, marketplace=args.marketplace, source=source)

    if args.format == 'json':
        print(json.dumps(report, indent=2))
    else:
        print(format_text_report(report))


if __name__ == '__main__':
    main()
