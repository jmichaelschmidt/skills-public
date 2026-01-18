#!/usr/bin/env python3
"""
Skill Inventory - Discover and list all Agent Skills across platforms.

Usage:
    inventory.py [options]

Options:
    --platform PLATFORM   Filter by platform: claude, codex, gemini, copilot, all (default: all)
    --format FORMAT       Output format: table, json, yaml (default: table)
    --verbose            Show full paths and metadata
    --include-marketplace Include marketplace skills (default: user skills only)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Default platform configuration
DEFAULT_PLATFORMS = {
    'claude': {
        'name': 'Claude Code',
        'global': '~/.claude/skills',
        'marketplace': '~/.claude/plugins/marketplaces',
    },
    'codex': {
        'name': 'OpenAI Codex',
        'global': '~/.codex/skills',
    },
    'gemini': {
        'name': 'Gemini CLI',
        'global': '~/.gemini/skills',
    },
    'copilot': {
        'name': 'GitHub Copilot',
        'global': '~/.copilot/skills',
    }
}


def load_config() -> dict:
    """Load configuration or return None."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return None


def get_platform_paths(config: dict = None) -> dict:
    """Return platform-specific skill directories."""
    paths = {}

    for platform_id, defaults in DEFAULT_PLATFORMS.items():
        paths[platform_id] = {
            'name': defaults['name'],
            'global': Path(defaults['global']).expanduser(),
        }
        if 'marketplace' in defaults:
            paths[platform_id]['marketplace'] = Path(defaults['marketplace']).expanduser()

    # Override with config values if present
    if config and 'platforms' in config:
        for platform_id, pconfig in config['platforms'].items():
            if platform_id in paths and pconfig.get('user_path'):
                paths[platform_id]['global'] = Path(pconfig['user_path']).expanduser()

    return paths


def parse_skill_frontmatter(skill_md_path: Path) -> Optional[dict]:
    """Parse YAML frontmatter from SKILL.md."""
    try:
        content = skill_md_path.read_text()
        if not content.startswith('---'):
            return None

        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return None

        # Simple YAML parsing for common fields
        frontmatter = {}
        for line in match.group(1).strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in ('name', 'description', 'license', 'compatibility'):
                    frontmatter[key] = value

        return frontmatter
    except Exception:
        return None


def discover_skills_in_directory(directory: Path, source_type: str = 'user') -> list:
    """Find all skills in a directory."""
    skills = []

    if not directory.exists():
        return skills

    for item in directory.iterdir():
        if item.is_dir():
            skill_md = item / 'SKILL.md'
            if skill_md.exists():
                frontmatter = parse_skill_frontmatter(skill_md)

                # Check if it's a symlink
                is_symlink = item.is_symlink()
                symlink_target = None
                if is_symlink:
                    try:
                        symlink_target = str(item.resolve())
                    except:
                        pass

                skills.append({
                    'name': frontmatter.get('name', item.name) if frontmatter else item.name,
                    'description': frontmatter.get('description', '') if frontmatter else '',
                    'path': str(item),
                    'source_type': source_type,
                    'valid': frontmatter is not None,
                    'is_symlink': is_symlink,
                    'symlink_target': symlink_target,
                })

    return skills


def discover_marketplace_skills(marketplace_dir: Path) -> list:
    """Find all skills in marketplace directories."""
    skills = []

    if not marketplace_dir.exists():
        return skills

    for marketplace in marketplace_dir.iterdir():
        if marketplace.is_dir():
            skills_dir = marketplace / 'skills'
            if skills_dir.exists():
                for skill in discover_skills_in_directory(skills_dir, 'marketplace'):
                    skill['marketplace'] = marketplace.name
                    skills.append(skill)

    return skills


def discover_all_skills(platforms: list, include_marketplace: bool = False, config: dict = None) -> dict:
    """Discover all skills across specified platforms."""
    paths = get_platform_paths(config)
    results = {}

    for platform in platforms:
        if platform not in paths:
            continue

        platform_skills = []
        platform_name = paths[platform].get('name', platform.upper())

        # User skills (global)
        if 'global' in paths[platform]:
            global_skills = discover_skills_in_directory(paths[platform]['global'], 'user')
            for skill in global_skills:
                skill['location'] = 'global'
            platform_skills.extend(global_skills)

        # Marketplace skills (Claude Code primarily)
        if include_marketplace and 'marketplace' in paths[platform]:
            marketplace_skills = discover_marketplace_skills(paths[platform]['marketplace'])
            for skill in marketplace_skills:
                skill['location'] = 'marketplace'
            platform_skills.extend(marketplace_skills)

        # Project skills (check current directory)
        cwd = Path.cwd()
        project_skills_dir = cwd / f'.{platform}' / 'skills'
        if project_skills_dir.exists():
            project_skills = discover_skills_in_directory(project_skills_dir, 'project')
            for skill in project_skills:
                skill['location'] = 'project'
                skill['project_path'] = str(cwd)
            platform_skills.extend(project_skills)

        results[platform] = {
            'name': platform_name,
            'skills': platform_skills
        }

    return results


def format_table(results: dict, verbose: bool = False) -> str:
    """Format results as a table."""
    lines = []

    for platform, data in results.items():
        skills = data['skills']
        platform_name = data['name']

        if not skills:
            lines.append(f"\n{platform_name}: No skills found")
            continue

        lines.append(f"\n{platform_name} ({len(skills)} skills)")
        lines.append("-" * 80)

        if verbose:
            lines.append(f"{'Name':<25} {'Location':<12} {'Type':<8} {'Path'}")
            lines.append("-" * 80)
            for skill in sorted(skills, key=lambda s: s['name']):
                link_marker = "→" if skill.get('is_symlink') else " "
                lines.append(f"{skill['name']:<25} {skill['location']:<12} {link_marker:<8} {skill['path']}")
                if skill.get('is_symlink') and skill.get('symlink_target'):
                    lines.append(f"{'':25} {'':12} {'':8} └→ {skill['symlink_target']}")
        else:
            lines.append(f"{'Name':<25} {'Location':<12} {'Description'}")
            lines.append("-" * 80)
            for skill in sorted(skills, key=lambda s: s['name']):
                desc = skill['description'][:40] + '...' if len(skill['description']) > 40 else skill['description']
                link_marker = " (→)" if skill.get('is_symlink') else ""
                lines.append(f"{skill['name']:<25} {skill['location']:<12} {desc}{link_marker}")

    # Summary
    total = sum(len(data['skills']) for data in results.values())
    platforms_with_skills = len([p for p, d in results.items() if d['skills']])
    lines.append(f"\nTotal: {total} skills across {platforms_with_skills} platforms")

    return '\n'.join(lines)


def format_json(results: dict) -> str:
    """Format results as JSON."""
    # Flatten for cleaner JSON output
    output = {}
    for platform, data in results.items():
        output[platform] = data['skills']
    return json.dumps(output, indent=2)


def format_yaml(results: dict) -> str:
    """Format results as YAML."""
    lines = []
    for platform, data in results.items():
        lines.append(f"{platform}:")
        for skill in data['skills']:
            lines.append(f"  - name: {skill['name']}")
            lines.append(f"    path: {skill['path']}")
            lines.append(f"    location: {skill['location']}")
            if skill.get('is_symlink'):
                lines.append(f"    symlink: true")
                if skill.get('symlink_target'):
                    lines.append(f"    target: {skill['symlink_target']}")
            if skill['description']:
                lines.append(f"    description: \"{skill['description'][:100]}\"")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Discover and list Agent Skills across platforms')
    parser.add_argument('--platform', choices=['claude', 'codex', 'gemini', 'copilot', 'all'], default='all',
                        help='Platform to search (default: all)')
    parser.add_argument('--format', choices=['table', 'json', 'yaml'], default='table',
                        help='Output format (default: table)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show full paths and metadata')
    parser.add_argument('--include-marketplace', action='store_true',
                        help='Include marketplace skills')

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Determine platforms to search
    if args.platform == 'all':
        platforms = list(DEFAULT_PLATFORMS.keys())
    else:
        platforms = [args.platform]

    # Discover skills
    results = discover_all_skills(platforms, args.include_marketplace, config)

    # Format and output
    if args.format == 'json':
        print(format_json(results))
    elif args.format == 'yaml':
        print(format_yaml(results))
    else:
        print(format_table(results, args.verbose))


if __name__ == '__main__':
    main()
