#!/usr/bin/env python3
"""
Marketplace Mirror - Mirror skills from a canonical marketplace into another marketplace.

Usage:
    marketplace-mirror.py mirror --from SOURCE --to TARGET --source-ref REF [options]
    marketplace-mirror.py drift --from SOURCE --to TARGET [--source-ref REF] [options]

Mirror options:
    --from NAME           Source marketplace key from config
    --to NAME             Target marketplace key from config
    --source-ref REF      Source tag/branch/commit to mirror
    --skill NAME          Skill name to mirror (repeatable; defaults to all skills at ref)
    --branch BRANCH       Target base branch override (defaults to remote HEAD)
    --message MSG         Custom commit message
    --no-pr               Skip PR creation (push only)
    --dry-run             Preview without writing

Drift options:
    --from NAME           Source marketplace key from config
    --to NAME             Target marketplace key from config
    --source-ref REF      Source tag/branch/commit (defaults to source default branch)
    --skill NAME          Limit drift check to specific skills (repeatable)
    --format text|json    Output format (default: text)

Examples:
    marketplace-mirror.py mirror --from public --to partner --source-ref v1.3.0
    marketplace-mirror.py mirror --from public --to partner --source-ref 8ab12cd --skill skill-manager
    marketplace-mirror.py drift --from public --to partner
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_resolver import load_config_required




def load_config() -> dict:
    """Load configuration."""
    return load_config_required()


def run_git(args: list, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run git command."""
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"ERROR: git {' '.join(args)} failed in {cwd}")
        if result.stderr.strip():
            print(result.stderr.strip())
        sys.exit(1)
    return result


def parse_repo_name(repo_url: str) -> str:
    """Extract repo name from URL and strip .git."""
    repo_name = repo_url.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def get_repo_path(config: dict, marketplace: str) -> Path:
    """Resolve local clone path for marketplace key."""
    marketplaces = config.get('marketplaces', {})
    if marketplace not in marketplaces:
        print(f"ERROR: Marketplace '{marketplace}' not found in config")
        print(f"Configured marketplaces: {', '.join(marketplaces.keys())}")
        sys.exit(1)

    repo_url = marketplaces[marketplace].get('repo', '')
    if not repo_url:
        print(f"ERROR: Marketplace '{marketplace}' has no repo configured")
        sys.exit(1)

    base_path = Path(config['local_repos_path']).expanduser()
    return base_path / parse_repo_name(repo_url)


def detect_default_branch(repo_path: Path, remote: str = 'origin') -> str:
    """Detect default branch from remote HEAD."""
    symbolic = run_git(['symbolic-ref', f'refs/remotes/{remote}/HEAD'], repo_path, check=False)
    if symbolic.returncode == 0:
        head = symbolic.stdout.strip()
        if head:
            return head.rsplit('/', 1)[-1]

    remote_show = run_git(['remote', 'show', remote], repo_path, check=False)
    if remote_show.returncode == 0:
        for line in remote_show.stdout.splitlines():
            line = line.strip()
            if line.startswith('HEAD branch:'):
                branch = line.split(':', 1)[1].strip()
                if branch and branch != '(unknown)':
                    return branch

    current = run_git(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path, check=False)
    if current.returncode == 0:
        branch = current.stdout.strip()
        if branch and branch != 'HEAD':
            return branch

    return 'main'


def ensure_repo_ready(repo_path: Path):
    """Ensure local repo exists and has no dirty state."""
    if not repo_path.exists():
        print(f"ERROR: Local repo missing: {repo_path}")
        print("Clone the repo or run scripts/init.py first.")
        sys.exit(1)

    status = run_git(['status', '--porcelain'], repo_path, check=False)
    if status.stdout.strip():
        print(f"ERROR: Uncommitted changes in {repo_path}")
        print("Commit or stash changes before mirroring.")
        sys.exit(1)


def resolve_plugin_name(manifest: dict, repo_path: Path) -> str:
    """Choose plugin name from manifest without key-based assumptions."""
    plugins = manifest.get('plugins') or []
    if len(plugins) == 1 and plugins[0].get('name'):
        return plugins[0]['name']

    manifest_name = manifest.get('name')
    if manifest_name:
        for plugin in plugins:
            if plugin.get('name') == manifest_name:
                return plugin['name']

    for plugin in plugins:
        if plugin.get('source') == './' and plugin.get('name'):
            return plugin['name']

    if manifest_name:
        return manifest_name

    return repo_path.name


def read_skill_description(skill_path: Path) -> str:
    """Parse description from SKILL.md frontmatter."""
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return ''

    content = skill_md.read_text()
    if not content.startswith('---'):
        return ''

    for line in content.split('\n')[1:]:
        if line.startswith('---'):
            break
        if line.startswith('description:'):
            return line.split(':', 1)[1].strip().strip('"').strip("'")

    return ''


def update_readme_row(content: str, skill_name: str, skill_description: str) -> tuple[str, bool]:
    """Insert or update one skill row in README table content."""
    table_marker = '## Available Skills'
    if table_marker not in content:
        return content, False

    short_description = skill_description
    if len(short_description) > 200:
        truncated = short_description[:200]
        last_period = truncated.rfind('.')
        if last_period > 100:
            short_description = truncated[:last_period + 1]
        else:
            short_description = truncated.rsplit(' ', 1)[0] + '...'

    new_row = f"| [{skill_name}](skills/{skill_name}/) | {short_description} |"
    skill_link_pattern = f"[{skill_name}](skills/{skill_name}/)"
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if skill_link_pattern in line:
            if line.strip() != new_row:
                lines[i] = new_row
                return '\n'.join(lines), True
            return content, False

    table_start = None
    table_header_end = None
    insert_index = None

    for i, line in enumerate(lines):
        if table_marker in line:
            table_start = i
        elif table_start is not None and line.startswith('|'):
            if '----' in line:
                table_header_end = i
            elif table_header_end is not None and line.startswith('| ['):
                existing_skill = line.split('](')[0].replace('| [', '')
                if skill_name.lower() < existing_skill.lower():
                    insert_index = i
                    break
        elif table_start is not None and table_header_end is not None and not line.startswith('|'):
            insert_index = i
            break

    if insert_index is None and table_header_end is not None:
        for i in range(len(lines) - 1, table_header_end, -1):
            if lines[i].startswith('|'):
                insert_index = i + 1
                break

    if insert_index is None:
        return content, False

    lines.insert(insert_index, new_row)
    return '\n'.join(lines), True


def update_readme(repo_path: Path, skill_descriptions: dict, dry_run: bool = False) -> bool:
    """Update README available skills table."""
    readme_path = repo_path / 'README.md'
    if not readme_path.exists():
        return False

    content = readme_path.read_text()
    updated = False

    for skill_name in sorted(skill_descriptions.keys()):
        content, changed = update_readme_row(content, skill_name, skill_descriptions[skill_name])
        updated = updated or changed

    if updated and not dry_run:
        readme_path.write_text(content)

    return updated


def update_manifest(repo_path: Path, target_marketplace: str, config: dict,
                    incoming_skills: list, dry_run: bool = False) -> tuple[str, str]:
    """Update marketplace manifest plugin skills and bump patch version."""
    manifest_path = repo_path / '.claude-plugin' / 'marketplace.json'
    if not manifest_path.exists():
        print(f"ERROR: Missing manifest: {manifest_path}")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    plugin_name = resolve_plugin_name(manifest, repo_path)

    plugin = None
    for entry in manifest.get('plugins', []):
        if entry.get('name') == plugin_name:
            plugin = entry
            break

    if plugin is None:
        plugin = {
            'name': plugin_name,
            'description': config['marketplaces'][target_marketplace]['description'],
            'source': './',
            'strict': False,
            'skills': []
        }
        manifest.setdefault('plugins', []).append(plugin)

    existing = set(plugin.get('skills', []))
    existing.update(f"./skills/{skill}" for skill in incoming_skills)
    plugin['skills'] = sorted(existing)

    metadata = manifest.setdefault('metadata', {})
    version = metadata.get('version', '1.0.0')
    parts = version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    metadata['version'] = '.'.join(parts)

    if not dry_run:
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')

    return metadata['version'], plugin_name


def create_source_worktree(source_repo: Path, source_ref: str) -> tuple[Path, Path]:
    """Create detached worktree at source ref and return (worktree_path, root_temp_dir)."""
    run_git(['rev-parse', '--verify', f'{source_ref}^{{commit}}'], source_repo)

    root = Path(tempfile.mkdtemp(prefix='skill-mirror-'))
    worktree_path = root / 'source'

    run_git(['worktree', 'add', '--detach', str(worktree_path), source_ref], source_repo)
    return worktree_path, root


def remove_source_worktree(source_repo: Path, worktree_path: Path, temp_root: Path):
    """Clean up temporary source worktree."""
    run_git(['worktree', 'remove', '--force', str(worktree_path)], source_repo, check=False)
    shutil.rmtree(temp_root, ignore_errors=True)


def list_skills_at_path(skills_dir: Path) -> list:
    """List skill directory names that contain SKILL.md."""
    if not skills_dir.exists():
        return []

    return sorted([
        item.name for item in skills_dir.iterdir()
        if item.is_dir() and (item / 'SKILL.md').exists()
    ])


def hash_skill_directory(skill_dir: Path) -> str:
    """Hash all files in a skill directory deterministically."""
    digest = hashlib.sha256()

    if not skill_dir.exists():
        return ''

    for file_path in sorted([p for p in skill_dir.rglob('*') if p.is_file()]):
        relative = file_path.relative_to(skill_dir).as_posix().encode()
        digest.update(relative)
        digest.update(b'\0')
        digest.update(hashlib.sha256(file_path.read_bytes()).digest())

    return digest.hexdigest()


def format_mirror_plan(source_marketplace: str, target_marketplace: str, source_ref: str,
                       source_commit: str, base_branch: str, selected_skills: list) -> str:
    """Format deterministic mirror plan output (used by dry-run and real execution)."""
    lines = [
        '=' * 70,
        'MARKETPLACE MIRROR',
        '=' * 70,
        f"Source: {source_marketplace} @ {source_ref} ({source_commit})",
        f"Target: {target_marketplace}",
        f"Base branch: {base_branch}",
        f"Skills: {', '.join(selected_skills)}",
    ]
    return '\n'.join(lines)


def mirror_skills(args):
    """Execute mirror workflow."""
    config = load_config()

    source_repo = get_repo_path(config, args.source_marketplace)
    target_repo = get_repo_path(config, args.target_marketplace)

    ensure_repo_ready(source_repo)
    ensure_repo_ready(target_repo)

    run_git(['fetch', 'origin'], source_repo, check=False)
    run_git(['fetch', 'origin'], target_repo, check=False)

    base_branch = args.branch or detect_default_branch(target_repo)
    source_ref = args.source_ref

    worktree_path = None
    temp_root = None

    try:
        worktree_path, temp_root = create_source_worktree(source_repo, source_ref)
        source_skills_dir = worktree_path / 'skills'
        available_skills = list_skills_at_path(source_skills_dir)

        if not available_skills:
            print(f"ERROR: No skills found at {args.source_marketplace}@{source_ref}")
            sys.exit(1)

        if args.skills:
            selected_skills = sorted(set(args.skills))
            missing = [skill for skill in selected_skills if skill not in available_skills]
            if missing:
                print(f"ERROR: Skills not found at source ref {source_ref}: {', '.join(missing)}")
                sys.exit(1)
        else:
            selected_skills = available_skills

        source_commit = run_git(['rev-parse', '--short', source_ref], source_repo).stdout.strip()
        branch_name = f"mirror-{args.source_marketplace}-to-{args.target_marketplace}-{source_commit}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        print(format_mirror_plan(
            args.source_marketplace,
            args.target_marketplace,
            source_ref,
            source_commit,
            base_branch,
            selected_skills,
        ))

        if args.dry_run:
            print('\n[DRY RUN MODE - No changes will be made]')
        else:
            checkout = run_git(['checkout', base_branch], target_repo, check=False)
            if checkout.returncode != 0:
                print(f"ERROR: Could not check out base branch '{base_branch}'")
                print('Use --branch to specify a valid branch.')
                sys.exit(1)

            run_git(['pull', 'origin', base_branch], target_repo, check=False)
            run_git(['checkout', '-B', branch_name, base_branch], target_repo)

        copied = []
        skill_descriptions = {}

        for skill_name in selected_skills:
            source_skill = source_skills_dir / skill_name
            target_skill = target_repo / 'skills' / skill_name

            if args.dry_run:
                print(f"  [DRY RUN] Would mirror skill: {skill_name}")
            else:
                target_skill.parent.mkdir(parents=True, exist_ok=True)
                if target_skill.exists():
                    shutil.rmtree(target_skill)
                shutil.copytree(source_skill, target_skill)
                copied.append(skill_name)

            skill_descriptions[skill_name] = read_skill_description(source_skill)

        if args.dry_run:
            print('  [DRY RUN] Would update .claude-plugin/marketplace.json')
            print('  [DRY RUN] Would update README.md skill table')
            new_version = '(dry-run)'
            plugin_name = '(dry-run)'
        else:
            new_version, plugin_name = update_manifest(
                target_repo,
                args.target_marketplace,
                config,
                selected_skills,
                dry_run=False,
            )
            readme_changed = update_readme(target_repo, skill_descriptions, dry_run=False)

            commit_message = args.message or (
                f"Mirror {len(selected_skills)} skill(s) from {args.source_marketplace}@{source_ref}"
            )
            run_git(['add', '.'], target_repo)
            run_git(['commit', '-m', commit_message], target_repo)
            run_git(['push', '-u', 'origin', branch_name], target_repo)

            print(f"\nManifest plugin: {plugin_name}")
            print(f"Manifest version: {new_version}")
            print(f"README updated: {'yes' if readme_changed else 'no changes'}")

        summary_lines = [
            '## Mirror Summary',
            f"- Source marketplace: `{args.source_marketplace}`",
            f"- Source ref: `{args.source_ref}`",
            f"- Resolved source commit: `{source_commit}`",
            f"- Target marketplace: `{args.target_marketplace}`",
            f"- Target base branch: `{base_branch}`",
            f"- Skills mirrored ({len(selected_skills)}): {', '.join(selected_skills)}",
            f"- Manifest version: `{new_version}`",
            '',
            '### Validation',
            f"- Source skills discovered: {len(available_skills)}",
            f"- Selected skills present at source ref: {len(selected_skills)}",
        ]

        summary_text = '\n'.join(summary_lines)
        print('\n' + '=' * 70)
        print('PR SUMMARY')
        print('=' * 70)
        print(summary_text)

        if not args.dry_run and not args.no_pr:
            pr_title = f"Mirror {len(selected_skills)} skill(s) from {args.source_marketplace}@{source_commit}"
            pr_result = subprocess.run(
                ['gh', 'pr', 'create', '--base', base_branch, '--title', pr_title, '--body', summary_text],
                cwd=target_repo,
                capture_output=True,
                text=True,
            )
            if pr_result.returncode == 0:
                print(f"\nCreated PR: {pr_result.stdout.strip()}")
            else:
                print('\nWARNING: PR creation failed; create manually with this summary.')
                print(pr_result.stderr.strip())

        if not args.dry_run:
            run_git(['checkout', base_branch], target_repo, check=False)

    finally:
        if worktree_path and temp_root:
            remove_source_worktree(source_repo, worktree_path, temp_root)


def drift_report(args):
    """Compare source and target skill hashes."""
    config = load_config()

    source_repo = get_repo_path(config, args.source_marketplace)
    target_repo = get_repo_path(config, args.target_marketplace)

    ensure_repo_ready(source_repo)
    ensure_repo_ready(target_repo)

    run_git(['fetch', 'origin'], source_repo, check=False)

    source_ref = args.source_ref
    if not source_ref:
        source_ref = detect_default_branch(source_repo)

    worktree_path = None
    temp_root = None

    try:
        worktree_path, temp_root = create_source_worktree(source_repo, source_ref)

        source_skills = list_skills_at_path(worktree_path / 'skills')
        target_skills = list_skills_at_path(target_repo / 'skills')

        if args.skills:
            skills = sorted(set(args.skills))
        else:
            skills = sorted(set(source_skills) | set(target_skills))

        rows = []
        drift_count = 0

        for skill in skills:
            source_skill_dir = worktree_path / 'skills' / skill
            target_skill_dir = target_repo / 'skills' / skill

            source_exists = source_skill_dir.exists() and (source_skill_dir / 'SKILL.md').exists()
            target_exists = target_skill_dir.exists() and (target_skill_dir / 'SKILL.md').exists()

            if not source_exists and not target_exists:
                status = 'missing-both'
                source_hash = ''
                target_hash = ''
            elif not source_exists:
                status = 'missing-source'
                source_hash = ''
                target_hash = hash_skill_directory(target_skill_dir)
                drift_count += 1
            elif not target_exists:
                status = 'missing-target'
                source_hash = hash_skill_directory(source_skill_dir)
                target_hash = ''
                drift_count += 1
            else:
                source_hash = hash_skill_directory(source_skill_dir)
                target_hash = hash_skill_directory(target_skill_dir)
                status = 'match' if source_hash == target_hash else 'drift'
                if status == 'drift':
                    drift_count += 1

            rows.append({
                'skill': skill,
                'status': status,
                'source_hash': source_hash,
                'target_hash': target_hash,
            })

        if args.format == 'json':
            payload = {
                'source_marketplace': args.source_marketplace,
                'target_marketplace': args.target_marketplace,
                'source_ref': source_ref,
                'total_skills': len(rows),
                'drift_count': drift_count,
                'rows': rows,
            }
            print(json.dumps(payload, indent=2))
        else:
            print('=' * 80)
            print('MARKETPLACE DRIFT REPORT')
            print('=' * 80)
            print(f"Source: {args.source_marketplace}@{source_ref}")
            print(f"Target: {args.target_marketplace}")
            print()
            print(f"{'Skill':<30} {'Status':<16} {'Source Hash':<16} {'Target Hash':<16}")
            print('-' * 80)
            for row in rows:
                print(
                    f"{row['skill']:<30} {row['status']:<16} "
                    f"{row['source_hash'][:12]:<16} {row['target_hash'][:12]:<16}"
                )

            print('\n' + '=' * 80)
            print(f"Total skills checked: {len(rows)}")
            print(f"Drift/missing count: {drift_count}")

        sys.exit(0 if drift_count == 0 else 1)

    finally:
        if worktree_path and temp_root:
            remove_source_worktree(source_repo, worktree_path, temp_root)


def main():
    parser = argparse.ArgumentParser(description='Mirror and drift-check marketplace skills')
    subparsers = parser.add_subparsers(dest='command', required=True)

    mirror_parser = subparsers.add_parser('mirror', help='Mirror skills to another marketplace')
    mirror_parser.add_argument('--from', dest='source_marketplace', required=True,
                               help='Source marketplace key from config')
    mirror_parser.add_argument('--to', dest='target_marketplace', required=True,
                               help='Target marketplace key from config')
    mirror_parser.add_argument('--source-ref', required=True,
                               help='Source tag/branch/commit to mirror from')
    mirror_parser.add_argument('--skill', dest='skills', action='append',
                               help='Skill to mirror (repeatable; defaults to all skills)')
    mirror_parser.add_argument('--branch',
                               help='Target base branch override')
    mirror_parser.add_argument('--message', '-m',
                               help='Custom commit message')
    mirror_parser.add_argument('--no-pr', action='store_true',
                               help='Skip PR creation')
    mirror_parser.add_argument('--dry-run', action='store_true',
                               help='Preview without writing')

    drift_parser = subparsers.add_parser('drift', help='Compare source and target skill hashes')
    drift_parser.add_argument('--from', dest='source_marketplace', required=True,
                              help='Source marketplace key from config')
    drift_parser.add_argument('--to', dest='target_marketplace', required=True,
                              help='Target marketplace key from config')
    drift_parser.add_argument('--source-ref',
                              help='Source tag/branch/commit (defaults to source default branch)')
    drift_parser.add_argument('--skill', dest='skills', action='append',
                              help='Skill to check (repeatable)')
    drift_parser.add_argument('--format', choices=['text', 'json'], default='text',
                              help='Output format')

    args = parser.parse_args()

    if args.command == 'mirror':
        mirror_skills(args)
    elif args.command == 'drift':
        drift_report(args)


if __name__ == '__main__':
    main()
