#!/usr/bin/env python3
"""
Skill Audit - Compare skills across platforms to detect drift and inconsistencies.

Usage:
    audit.py <skill-name>           Audit a specific skill across platforms
    audit.py --all                  Audit all skills for cross-platform consistency
    audit.py --source <path> --compare <platform>  Compare source against platform

Options:
    --format FORMAT    Output format: text, json (default: text)
    --verbose          Show detailed file-by-file comparison
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


def get_platform_paths():
    """Return platform-specific skill directories."""
    home = Path.home()
    return {
        'claude': home / '.claude' / 'skills',
        'codex': home / '.codex' / 'skills',
    }


def hash_file(path: Path) -> str:
    """Calculate MD5 hash of a file."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return "ERROR"


def get_skill_files(skill_path: Path) -> dict:
    """Get all files in a skill with their hashes."""
    files = {}
    if not skill_path.exists():
        return files

    for item in skill_path.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(skill_path)
            files[str(rel_path)] = {
                'hash': hash_file(item),
                'size': item.stat().st_size,
                'path': str(item),
            }
    return files


def parse_skill_metadata(skill_path: Path) -> Optional[dict]:
    """Extract metadata from SKILL.md."""
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text()
        if not content.startswith('---'):
            return {'raw': True}

        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {'raw': True}

        # Parse basic fields
        metadata = {}
        for line in match.group(1).strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")
        return metadata
    except Exception:
        return None


def find_skill_across_platforms(skill_name: str) -> dict:
    """Find a skill by name across all platforms."""
    paths = get_platform_paths()
    found = {}

    for platform, base_path in paths.items():
        skill_path = base_path / skill_name
        if skill_path.exists():
            found[platform] = {
                'path': skill_path,
                'files': get_skill_files(skill_path),
                'metadata': parse_skill_metadata(skill_path),
                'is_symlink': skill_path.is_symlink(),
                'symlink_target': str(skill_path.resolve()) if skill_path.is_symlink() else None,
            }

    return found


def compare_skill_versions(skill_data: dict, verbose: bool = False) -> dict:
    """Compare skill versions across platforms."""
    if len(skill_data) < 2:
        return {
            'status': 'single',
            'message': 'Skill only exists on one platform',
            'platforms': list(skill_data.keys()),
        }

    platforms = list(skill_data.keys())
    base_platform = platforms[0]
    base_files = skill_data[base_platform]['files']

    comparison = {
        'status': 'ok',
        'platforms': platforms,
        'differences': [],
        'missing_files': {},
        'extra_files': {},
        'modified_files': {},
    }

    # Check symlink status
    symlinks = {p: d['is_symlink'] for p, d in skill_data.items()}
    if any(symlinks.values()):
        targets = {p: d['symlink_target'] for p, d in skill_data.items() if d['is_symlink']}

        # All are symlinks to same location
        if len(set(targets.values())) == 1 and all(symlinks.values()):
            comparison['status'] = 'synced'
            comparison['message'] = 'All platforms symlinked to same source'
            comparison['symlink_target'] = list(targets.values())[0]
            return comparison

        # Some are symlinks, check if they point to a non-symlink version
        non_symlink_paths = {p: str(d['path']) for p, d in skill_data.items() if not d['is_symlink']}
        for platform, target in targets.items():
            if target in non_symlink_paths.values():
                comparison['status'] = 'synced'
                comparison['message'] = f"Platforms synced via symlinks"
                comparison['symlink_info'] = {
                    'symlinks': {p: t for p, t in targets.items()},
                    'sources': non_symlink_paths,
                }
                return comparison

    # Compare files between platforms
    for platform in platforms[1:]:
        other_files = skill_data[platform]['files']

        # Find missing files
        missing = set(base_files.keys()) - set(other_files.keys())
        if missing:
            comparison['missing_files'][platform] = list(missing)
            comparison['status'] = 'drift'

        # Find extra files
        extra = set(other_files.keys()) - set(base_files.keys())
        if extra:
            comparison['extra_files'][platform] = list(extra)
            comparison['status'] = 'drift'

        # Find modified files
        common = set(base_files.keys()) & set(other_files.keys())
        modified = []
        for f in common:
            if base_files[f]['hash'] != other_files[f]['hash']:
                modified.append({
                    'file': f,
                    f'{base_platform}_hash': base_files[f]['hash'],
                    f'{platform}_hash': other_files[f]['hash'],
                })
        if modified:
            comparison['modified_files'][platform] = modified
            comparison['status'] = 'drift'

    return comparison


def audit_all_skills() -> dict:
    """Audit all skills across platforms."""
    paths = get_platform_paths()
    all_skills = set()

    # Collect all skill names
    for platform, base_path in paths.items():
        if base_path.exists():
            for item in base_path.iterdir():
                if item.is_dir() and (item / 'SKILL.md').exists():
                    all_skills.add(item.name)

    results = {}
    for skill_name in sorted(all_skills):
        skill_data = find_skill_across_platforms(skill_name)
        comparison = compare_skill_versions(skill_data)
        results[skill_name] = {
            'platforms': list(skill_data.keys()),
            'comparison': comparison,
        }

    return results


def format_text_output(results: dict, verbose: bool = False) -> str:
    """Format audit results as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("SKILL AUDIT REPORT")
    lines.append("=" * 60)

    drift_count = 0
    synced_count = 0
    single_count = 0

    for skill_name, data in results.items():
        comparison = data['comparison']
        status = comparison['status']

        if status == 'drift':
            drift_count += 1
            status_icon = "DRIFT"
        elif status == 'synced':
            synced_count += 1
            status_icon = "SYNCED"
        elif status == 'single':
            single_count += 1
            status_icon = "SINGLE"
        else:
            status_icon = "OK"

        lines.append(f"\n[{status_icon}] {skill_name}")
        lines.append(f"    Platforms: {', '.join(data['platforms'])}")

        if verbose or status == 'drift':
            if comparison.get('message'):
                lines.append(f"    {comparison['message']}")
            if comparison.get('symlink_target'):
                lines.append(f"    Symlink target: {comparison['symlink_target']}")
            if comparison.get('missing_files'):
                for platform, files in comparison['missing_files'].items():
                    lines.append(f"    Missing on {platform}: {', '.join(files)}")
            if comparison.get('extra_files'):
                for platform, files in comparison['extra_files'].items():
                    lines.append(f"    Extra on {platform}: {', '.join(files)}")
            if comparison.get('modified_files'):
                for platform, files in comparison['modified_files'].items():
                    lines.append(f"    Modified on {platform}:")
                    for f in files:
                        lines.append(f"      - {f['file']}")

    # Summary
    lines.append("\n" + "=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Total skills audited: {len(results)}")
    lines.append(f"  Synced (symlinked):  {synced_count}")
    lines.append(f"  OK (identical):      {len(results) - drift_count - synced_count - single_count}")
    lines.append(f"  Drift detected:      {drift_count}")
    lines.append(f"  Single platform:     {single_count}")

    if drift_count > 0:
        lines.append("\nWARNING: Drift detected! Use 'sync.py' to reconcile differences.")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Audit skills across platforms for drift')
    parser.add_argument('skill_name', nargs='?',
                        help='Name of skill to audit')
    parser.add_argument('--all', action='store_true',
                        help='Audit all skills')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                        help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed comparison')

    args = parser.parse_args()

    if args.all:
        results = audit_all_skills()
    elif args.skill_name:
        skill_data = find_skill_across_platforms(args.skill_name)
        if not skill_data:
            print(f"ERROR: Skill '{args.skill_name}' not found on any platform")
            sys.exit(1)
        comparison = compare_skill_versions(skill_data, args.verbose)
        results = {args.skill_name: {'platforms': list(skill_data.keys()), 'comparison': comparison}}
    else:
        parser.print_help()
        sys.exit(1)

    if args.format == 'json':
        # Convert Path objects to strings for JSON serialization
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_text_output(results, args.verbose))


if __name__ == '__main__':
    main()
