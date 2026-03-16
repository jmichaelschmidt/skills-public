#!/usr/bin/env python3
"""
Skill Publish - Publish skills to marketplace repositories.

Usage:
    publish.py <skill-path> [--to <marketplace>] [options]

Options:
    --to MARKETPLACE    Target marketplace name from config (prompts if not specified)
    --branch BRANCH     Use this branch as the base branch (defaults to remote HEAD)
    --in-development    Publish to skills-in-development/ and skip marketplace manifest updates
    --dry-run           Preview changes without applying
    --no-pr             Skip creating a pull request (just push to branch)
    --message MSG       Custom commit message

Examples:
    publish.py ~/.claude/skills/my-skill --to team
    publish.py ~/.claude/skills/my-skill --to partner --in-development
    publish.py ./my-skill --to public --dry-run
    publish.py ~/.claude/skills/my-skill --to project-x
    publish.py ~/.claude/skills/my-skill  # Will prompt for marketplace
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_resolver import load_config_required
from datetime import datetime


PUBLISHED_SKILLS_DIR = 'skills'
IN_DEVELOPMENT_SKILLS_DIR = 'skills-in-development'


def load_config() -> dict:
    """Load configuration."""
    return load_config_required()


def parse_repo_name(repo_url: str) -> str:
    """Extract repo name from a URL and strip optional .git."""
    repo_name = repo_url.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def get_local_repo_path(config: dict, marketplace: str) -> Path:
    """Get the local clone path for a marketplace repo."""
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'][marketplace].get('repo', '')
    if repo_url:
        return base_path / parse_repo_name(repo_url)
    # Marketplace key is a safer fallback than assuming skills-{key}
    return base_path / marketplace


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


def infer_in_development(skill_path: Path) -> bool:
    """Infer development-mode publish target from source path."""
    return IN_DEVELOPMENT_SKILLS_DIR in skill_path.parts


def parse_skill_name(skill_path: Path) -> str:
    """Extract skill name from SKILL.md frontmatter."""
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text()

    if not content.startswith('---'):
        return skill_path.name

    for line in content.split('\n')[1:]:
        if line.startswith('---'):
            break
        if line.startswith('name:'):
            return line.split(':', 1)[1].strip().strip('"').strip("'")

    return skill_path.name


def prompt_for_marketplace(config: dict) -> str:
    """Interactively ask user which marketplace to publish to."""
    marketplaces = config.get('marketplaces', {})
    configured = [(name, info) for name, info in marketplaces.items() if info.get('repo')]

    if not configured:
        print("ERROR: No marketplaces configured with repo URLs.")
        print("Run 'scripts/init.py' to configure your marketplaces.")
        sys.exit(1)

    print("\nWhich marketplace should this skill be published to?")
    for i, (name, info) in enumerate(configured, 1):
        desc = info.get('description', 'No description')
        visibility = info.get('visibility', 'unknown')
        print(f"  {i}. {name} - {desc} ({visibility})")

    name_map = {str(i): name for i, (name, _) in enumerate(configured, 1)}
    name_map.update({name: name for name, _ in configured})

    while True:
        response = input(f"\nSelect marketplace (1-{len(configured)} or name): ").strip().lower()
        if response in name_map:
            return name_map[response]
        print(f"Invalid selection. Please enter 1-{len(configured)} or marketplace name.")


def run_git_command(args: list, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"Git command failed: git {' '.join(args)}")
        print(f"stderr: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    return result


def detect_default_branch(repo_path: Path, remote: str = 'origin') -> str:
    """Detect repository default branch from origin/HEAD."""
    symbolic = run_git_command(
        ['symbolic-ref', f'refs/remotes/{remote}/HEAD'],
        repo_path,
        check=False
    )
    if symbolic.returncode == 0:
        head_ref = symbolic.stdout.strip()
        if head_ref:
            return head_ref.rsplit('/', 1)[-1]

    remote_show = run_git_command(['remote', 'show', remote], repo_path, check=False)
    if remote_show.returncode == 0:
        for line in remote_show.stdout.splitlines():
            line = line.strip()
            if line.startswith('HEAD branch:'):
                branch = line.split(':', 1)[1].strip()
                if branch and branch != '(unknown)':
                    return branch

    current = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'], repo_path, check=False)
    if current.returncode == 0:
        branch = current.stdout.strip()
        if branch and branch != 'HEAD':
            return branch

    return 'main'


def has_uncommitted_changes(repo_path: Path) -> bool:
    """Return True when git status has tracked or untracked changes."""
    status = run_git_command(['status', '--porcelain'], repo_path, check=False)
    return bool(status.stdout.strip())


def ensure_repo_cloned(config: dict, marketplace: str, branch_override: str = None) -> tuple[Path, str]:
    """Ensure the marketplace repo is cloned locally and synced to base branch."""
    repo_url = config['marketplaces'][marketplace]['repo']
    if not repo_url:
        print(f"ERROR: No repository configured for marketplace '{marketplace}'")
        print("Run 'scripts/init.py' to configure your marketplace repositories.")
        sys.exit(1)

    local_path = get_local_repo_path(config, marketplace)

    if local_path.exists():
        if has_uncommitted_changes(local_path):
            print(f"ERROR: Uncommitted changes detected in {local_path}")
            print("Commit or stash those changes before running publish.")
            sys.exit(1)

        print(f"Updating local repo: {local_path}")
        run_git_command(['fetch', 'origin'], local_path)
    else:
        print(f"Cloning {repo_url} to {local_path}")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', repo_url, str(local_path)], check=True)
        run_git_command(['fetch', 'origin'], local_path, check=False)

    base_branch = branch_override or detect_default_branch(local_path)

    checkout_result = run_git_command(['checkout', base_branch], local_path, check=False)
    if checkout_result.returncode != 0:
        print(f"ERROR: Could not check out base branch '{base_branch}' in {local_path}")
        print("Use --branch to select a different base branch.")
        sys.exit(1)

    run_git_command(['pull', 'origin', base_branch], local_path, check=False)
    return local_path, base_branch


def resolve_plugin_name(marketplace: dict, repo_path: Path) -> str:
    """Derive plugin name from existing manifest instead of marketplace key assumptions."""
    plugins = marketplace.get('plugins') or []
    if len(plugins) == 1 and plugins[0].get('name'):
        return plugins[0]['name']

    manifest_name = marketplace.get('name')
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


def update_marketplace_json(repo_path: Path, skill_name: str, skill_description: str, marketplace_name: str, config: dict):
    """Update marketplace.json to include the new skill and return version."""
    marketplace_json_path = repo_path / '.claude-plugin' / 'marketplace.json'

    if not marketplace_json_path.exists():
        print(f"ERROR: marketplace.json not found at {marketplace_json_path}")
        print("The repository may not be properly initialized as a marketplace.")
        sys.exit(1)

    with open(marketplace_json_path) as f:
        marketplace = json.load(f)

    plugin_name = resolve_plugin_name(marketplace, repo_path)

    plugin = None
    for entry in marketplace.get('plugins', []):
        if entry.get('name') == plugin_name:
            plugin = entry
            break

    if plugin is None:
        plugin = {
            'name': plugin_name,
            'description': config['marketplaces'][marketplace_name]['description'],
            'source': './',
            'strict': False,
            'skills': []
        }
        marketplace.setdefault('plugins', []).append(plugin)

    skill_path = f"./skills/{skill_name}"
    if skill_path not in plugin.get('skills', []):
        plugin.setdefault('skills', []).append(skill_path)
        plugin['skills'].sort()

    if 'metadata' in marketplace:
        version = marketplace['metadata'].get('version', '1.0.0')
        parts = version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        marketplace['metadata']['version'] = '.'.join(parts)

    with open(marketplace_json_path, 'w') as f:
        json.dump(marketplace, f, indent=2)

    return marketplace.get('metadata', {}).get('version', '1.0.0')


def update_readme(repo_path: Path, skill_name: str, skill_description: str, dry_run: bool = False) -> bool:
    """Update README Available Skills table. Returns True if README changed."""
    readme_path = repo_path / 'README.md'

    if not readme_path.exists():
        if not dry_run:
            print(f"  Warning: README.md not found at {readme_path}, skipping README update")
        return False

    content = readme_path.read_text()
    table_marker = "## Available Skills"
    if table_marker not in content:
        if not dry_run:
            print("  Warning: No '## Available Skills' section found in README.md, skipping")
        return False

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

    if skill_link_pattern in content:
        lines = content.split('\n')
        updated = False
        for i, line in enumerate(lines):
            if skill_link_pattern in line:
                if line.strip() != new_row:
                    lines[i] = new_row
                    updated = True
                    if dry_run:
                        print("  [DRY RUN] Would update skill description in README.md")
                    else:
                        print("  Updated skill description in README.md")
                break

        if updated and not dry_run:
            readme_path.write_text('\n'.join(lines))
        return updated

    lines = content.split('\n')
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
        if not dry_run:
            print("  Warning: Could not find proper location in README.md table, skipping")
        return False

    if dry_run:
        print("  [DRY RUN] Would add skill to README.md Available Skills table")
    else:
        lines.insert(insert_index, new_row)
        readme_path.write_text('\n'.join(lines))
        print("  Added skill to README.md Available Skills table")

    return True


def create_symlink_to_codex(skill_path: Path, skill_name: str, dry_run: bool = False):
    """Create a symlink in the Codex skills directory."""
    codex_skills_dir = Path.home() / '.codex' / 'skills'
    codex_skill_path = codex_skills_dir / skill_name

    if dry_run:
        print(f"  [DRY RUN] Would symlink {codex_skill_path} -> {skill_path}")
        return

    codex_skills_dir.mkdir(parents=True, exist_ok=True)

    if codex_skill_path.exists() or codex_skill_path.is_symlink():
        if codex_skill_path.is_symlink():
            codex_skill_path.unlink()
        else:
            shutil.rmtree(codex_skill_path)

    codex_skill_path.symlink_to(skill_path.resolve())
    print(f"  Symlinked to Codex: {codex_skill_path} -> {skill_path}")


def repo_slug_from_url(repo_url: str) -> str:
    """Return owner/repo from a URL."""
    clean = repo_url.rstrip('/').replace('.git', '')
    parts = clean.split('/')
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return clean


def publish_skill(skill_path: Path, marketplace: str, config: dict,
                  dry_run: bool = False, no_pr: bool = False,
                  custom_message: str = None, branch_override: str = None,
                  in_development: bool = False) -> dict:
    """Publish a skill to the specified marketplace."""
    skill_name = parse_skill_name(skill_path)

    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text()
    description = ""
    if content.startswith('---'):
        for line in content.split('\n')[1:]:
            if line.startswith('---'):
                break
            if line.startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"').strip("'")

    print(f"\nPublishing skill: {skill_name}")
    print(f"Source: {skill_path}")
    print(f"Marketplace: {marketplace}")
    publish_dir = IN_DEVELOPMENT_SKILLS_DIR if in_development else PUBLISHED_SKILLS_DIR
    print(f"Destination Folder: {publish_dir}")

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    results = {
        'skill_name': skill_name,
        'marketplace': marketplace,
        'success': False,
        'pr_url': None,
        'version': None,
        'base_branch': None,
        'publish_dir': publish_dir,
        'manifest_updated': False,
        'in_development': in_development,
    }

    if not dry_run:
        repo_path, base_branch = ensure_repo_cloned(config, marketplace, branch_override)
    else:
        repo_path = get_local_repo_path(config, marketplace)
        base_branch = branch_override or 'remote-default'
        print(f"  [DRY RUN] Would clone/update repo at {repo_path}")

    results['base_branch'] = base_branch

    branch_name = f"publish-{skill_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    if not dry_run:
        run_git_command(['checkout', '-B', branch_name, base_branch], repo_path)
        print(f"  Created branch: {branch_name} (from {base_branch})")
    else:
        print(f"  [DRY RUN] Would create branch: {branch_name} from {base_branch}")

    target_skill_path = repo_path / publish_dir / skill_name
    if not dry_run:
        target_skill_path.parent.mkdir(parents=True, exist_ok=True)
        if target_skill_path.exists():
            shutil.rmtree(target_skill_path)
        shutil.copytree(skill_path, target_skill_path)
        print(f"  Copied skill to: {target_skill_path}")
    else:
        print(f"  [DRY RUN] Would copy skill to: {target_skill_path}")

    if in_development and not dry_run:
        print("  Skipping marketplace.json update (in-development publish)")
    elif in_development:
        print("  [DRY RUN] Would skip marketplace.json update (in-development publish)")
    elif not dry_run:
        new_version = update_marketplace_json(repo_path, skill_name, description, marketplace, config)
        results['version'] = new_version
        results['manifest_updated'] = True
        print(f"  Updated marketplace.json (version: {new_version})")
    else:
        print("  [DRY RUN] Would update marketplace.json")

    if in_development:
        if dry_run:
            print("  [DRY RUN] Would skip README auto-update for in-development publish")
        else:
            print("  Skipping README auto-update for in-development publish")
    else:
        update_readme(repo_path, skill_name, description, dry_run)

    commit_message = custom_message or (
        f"Add {skill_name} skill (in development)" if in_development else f"Add {skill_name} skill"
    )
    if not dry_run:
        run_git_command(['add', '.'], repo_path)
        run_git_command(['commit', '-m', commit_message], repo_path)
        print(f"  Committed: {commit_message}")
    else:
        print(f"  [DRY RUN] Would commit: {commit_message}")

    if not dry_run:
        run_git_command(['push', '-u', 'origin', branch_name], repo_path)
        print("  Pushed branch to origin")
    else:
        print("  [DRY RUN] Would push branch to origin")

    if not no_pr and not dry_run:
        try:
            pr_title = (
                f"Add {skill_name} skill (in development)"
                if in_development else f"Add {skill_name} skill"
            )
            pr_body = (
                "## Summary\n\n"
                f"Adds the `{skill_name}` skill to `{publish_dir}` in the {marketplace} repository.\n\n"
                f"**Description:** {description[:200]}\n\n"
                "**Manifest:** skipped (in development)"
                if in_development else
                "## Summary\n\n"
                f"Adds the `{skill_name}` skill to the {marketplace} marketplace.\n\n"
                f"**Description:** {description[:200]}"
            )
            pr_result = subprocess.run(
                ['gh', 'pr', 'create',
                 '--base', base_branch,
                 '--title', pr_title,
                 '--body', pr_body],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if pr_result.returncode == 0:
                pr_url = pr_result.stdout.strip()
                results['pr_url'] = pr_url
                print(f"  Created PR: {pr_url}")
            else:
                print(f"  Warning: Could not create PR via gh CLI: {pr_result.stderr}")
                print("  You can create it manually at the repository.")
        except FileNotFoundError:
            print("  Warning: gh CLI not found. Create PR manually.")
    elif not no_pr:
        print("  [DRY RUN] Would create PR")

    if config.get('codex_symlink', True):
        create_symlink_to_codex(skill_path, skill_name, dry_run)

    if not dry_run:
        run_git_command(['checkout', base_branch], repo_path)

    results['success'] = True
    return results


def main():
    parser = argparse.ArgumentParser(description='Publish skills to marketplace repositories')
    parser.add_argument('skill_path', type=Path,
                        help='Path to the skill directory to publish')
    parser.add_argument('--to', dest='marketplace',
                        help='Target marketplace name from config (prompts if not specified)')
    parser.add_argument('--branch',
                        help='Base branch override (defaults to remote HEAD branch)')
    parser.add_argument('--in-development', action='store_true',
                        help='Publish to skills-in-development/ and skip marketplace manifest updates')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--no-pr', action='store_true',
                        help='Skip creating a pull request')
    parser.add_argument('--message', '-m',
                        help='Custom commit message')

    args = parser.parse_args()

    config = load_config()
    skill_path = args.skill_path.resolve()

    valid, message = validate_source_skill(skill_path)
    if not valid:
        print(f"ERROR: {message}")
        sys.exit(1)

    marketplace = args.marketplace
    if not marketplace:
        marketplace = prompt_for_marketplace(config)

    if marketplace not in config.get('marketplaces', {}):
        print(f"\nERROR: Marketplace '{marketplace}' not found in config.")
        print(f"Available marketplaces: {', '.join(config.get('marketplaces', {}).keys())}")
        sys.exit(1)

    if not config['marketplaces'][marketplace].get('repo'):
        print(f"\nERROR: No repository configured for marketplace '{marketplace}'")
        print("Run 'scripts/init.py' to configure your marketplace repositories.")
        sys.exit(1)

    inferred_in_development = infer_in_development(skill_path)
    in_development = args.in_development or inferred_in_development
    if inferred_in_development and not args.in_development:
        print(f"Detected '{IN_DEVELOPMENT_SKILLS_DIR}' in source path; enabling in-development mode.")

    results = publish_skill(
        skill_path,
        marketplace,
        config,
        dry_run=args.dry_run,
        no_pr=args.no_pr,
        custom_message=args.message,
        branch_override=args.branch,
        in_development=in_development,
    )

    print("\n" + "=" * 50)
    print("PUBLISH SUMMARY")
    print("=" * 50)
    print(f"Skill: {results['skill_name']}")
    print(f"Marketplace: {results['marketplace']}")
    print(f"Base Branch: {results['base_branch']}")
    print(f"Destination Folder: {results['publish_dir']}")
    print(f"Manifest Updated: {'Yes' if results['manifest_updated'] else 'No'}")
    print(f"Success: {'Yes' if results['success'] else 'No'}")
    if results['version']:
        print(f"Marketplace Version: {results['version']}")
    if results['pr_url']:
        print(f"PR URL: {results['pr_url']}")

    if results['success'] and not args.dry_run:
        repo_url = config['marketplaces'][results['marketplace']].get('repo', '')
        repo_slug = repo_slug_from_url(repo_url)

        print("\n" + "-" * 50)
        print("NEXT STEPS:")
        print("-" * 50)
        if results['pr_url']:
            print(f"1. Review and merge the PR: {results['pr_url']}")
        if results['in_development']:
            print(f"2. Keep `{results['skill_name']}` in `{IN_DEVELOPMENT_SKILLS_DIR}/` until approved.")
            print("3. Promote to `skills/` and update marketplace.json only when ready for install.")
        else:
            print(f"2. Once merged, users can install via:")
            print(f"   /plugin marketplace add {repo_slug}")
        print("-" * 50)

    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
