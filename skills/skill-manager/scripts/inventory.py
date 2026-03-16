#!/usr/bin/env python3
"""
Skill Inventory - Discover and list all Agent Skills across platforms.

Usage:
    inventory.py [options]

Options:
    --platform PLATFORM   Filter by platform: claude, codex, gemini, copilot, all (default: all)
    --format FORMAT       Output format: table, json, yaml (default: table)
    --verbose            Show full paths and metadata
    --source SOURCE      Include sources: all, global, project, marketplace (repeatable)
    --exclude-source     Exclude sources: global, project, marketplace (repeatable)
    --global-only        Only show global skills
    --project-only       Only show project skills
    --marketplace-only   Only show marketplace skills
    --no-marketplace     Exclude marketplace skills
    --include-marketplace Backward-compatible alias (marketplace is included by default)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_resolver import load_config_optional
from typing import Optional


ALL_SOURCES = {'global', 'project', 'marketplace'}

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
    return load_config_optional()


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


def discover_all_skills(platforms: list, include_sources: set = None, config: dict = None) -> dict:
    """Discover all skills across specified platforms."""
    paths = get_platform_paths(config)
    results = {}
    if include_sources is None:
        include_sources = set(ALL_SOURCES)

    for platform in platforms:
        if platform not in paths:
            continue

        platform_skills = []
        platform_name = paths[platform].get('name', platform.upper())

        # User skills (global)
        if 'global' in include_sources and 'global' in paths[platform]:
            global_skills = discover_skills_in_directory(paths[platform]['global'], 'user')
            for skill in global_skills:
                skill['location'] = 'global'
            platform_skills.extend(global_skills)

        # Marketplace skills (Claude Code primarily)
        if 'marketplace' in include_sources and 'marketplace' in paths[platform]:
            marketplace_skills = discover_marketplace_skills(paths[platform]['marketplace'])
            for skill in marketplace_skills:
                skill['location'] = 'marketplace'
            platform_skills.extend(marketplace_skills)

        # Project skills (check current directory)
        if 'project' in include_sources:
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


def normalize_legacy_args(argv: list) -> list:
    """Translate common legacy CLI variants to current flags."""
    normalized = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        # Support: --include marketplace
        if arg == '--include' and i + 1 < len(argv):
            value = argv[i + 1].strip().lower()
            if value == 'marketplace':
                normalized.append('--include-marketplace')
                i += 2
                continue

        # Support: --include=marketplace
        if arg.startswith('--include='):
            value = arg.split('=', 1)[1].strip().lower()
            if value == 'marketplace':
                normalized.append('--include-marketplace')
                i += 1
                continue

        normalized.append(arg)
        i += 1

    return normalized


def resolve_sources(args) -> set:
    """Resolve include/exclude source flags into the final source set."""
    if args.source and 'all' not in args.source:
        include_sources = set(args.source)
    else:
        include_sources = set(ALL_SOURCES)

    if args.global_only:
        include_sources = {'global'}
    if args.project_only:
        include_sources = {'project'}
    if args.marketplace_only:
        include_sources = {'marketplace'}

    # Backward-compatible flag. Marketplace is already included by default.
    if args.include_marketplace:
        include_sources.add('marketplace')

    if args.no_marketplace:
        include_sources.discard('marketplace')

    if args.exclude_source:
        include_sources -= set(args.exclude_source)

    return include_sources


class SkillInventoryParser(argparse.ArgumentParser):
    """ArgumentParser with actionable error guidance for common mistakes."""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)

        if '--include' in message or 'unrecognized arguments' in message:
            print(
                "Hint: use --include-marketplace "
                "(legacy aliases --include marketplace and --include=marketplace are supported).",
                file=sys.stderr
            )

        print(
            "Example: inventory.py --platform claude --source marketplace",
            file=sys.stderr
        )
        self.exit(2)


def main():
    parser = SkillInventoryParser(description='Discover and list Agent Skills across platforms')
    parser.add_argument('--platform', choices=['claude', 'codex', 'gemini', 'copilot', 'all'], default='all',
                        help='Platform to search (default: all)')
    parser.add_argument('--format', choices=['table', 'json', 'yaml'], default='table',
                        help='Output format (default: table)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show full paths and metadata')
    parser.add_argument('--source', action='append', choices=['all', 'global', 'project', 'marketplace'],
                        help='Include only selected source(s). Repeatable.')
    parser.add_argument('--exclude-source', action='append', choices=['global', 'project', 'marketplace'],
                        help='Exclude selected source(s). Repeatable.')
    parser.add_argument('--global-only', action='store_true',
                        help='Only show global skills')
    parser.add_argument('--project-only', action='store_true',
                        help='Only show project skills')
    parser.add_argument('--marketplace-only', action='store_true',
                        help='Only show marketplace skills')
    parser.add_argument('--no-marketplace', action='store_true',
                        help='Exclude marketplace skills')
    parser.add_argument('--include-marketplace', action='store_true',
                        help='Backward-compatible alias; marketplace is included by default')

    args = parser.parse_args(normalize_legacy_args(sys.argv[1:]))

    # Load config
    config = load_config()

    # Determine platforms to search
    if args.platform == 'all':
        platforms = list(DEFAULT_PLATFORMS.keys())
    else:
        platforms = [args.platform]

    include_sources = resolve_sources(args)

    # Discover skills
    results = discover_all_skills(platforms, include_sources, config)

    # Format and output
    if args.format == 'json':
        print(format_json(results))
    elif args.format == 'yaml':
        print(format_yaml(results))
    else:
        print(format_table(results, args.verbose))


if __name__ == '__main__':
    main()
