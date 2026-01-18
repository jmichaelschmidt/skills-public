#!/usr/bin/env python3
"""
Skill Manager Init - Set up platforms and marketplace repositories.

Usage:
    init.py [options]

Options:
    --skip-create       Skip creating new GitHub repos (configure existing ones)
    --skip-marketplaces Skip marketplace setup (only configure platforms)
    --org ORG           GitHub organization for team/public repos

This script will:
1. Detect installed AI platforms (Claude, Codex, Gemini, Copilot)
2. Configure which platform is your source of truth
3. Set up sync preferences (symlink vs copy)
4. Optionally configure marketplace repositories for skill distribution

Examples:
    init.py                      # Full interactive setup
    init.py --skip-marketplaces  # Just configure platform sync
    init.py --org my-org         # Use specific org for team/public repos
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Supported platforms with their default paths
PLATFORMS = {
    'claude': {
        'name': 'Claude Code',
        'user_path': '~/.claude/skills',
        'detect_path': '~/.claude',
        'description': 'Anthropic Claude Code CLI'
    },
    'codex': {
        'name': 'OpenAI Codex',
        'user_path': '~/.codex/skills',
        'detect_path': '~/.codex',
        'description': 'OpenAI Codex CLI'
    },
    'gemini': {
        'name': 'Gemini CLI',
        'user_path': '~/.gemini/skills',
        'detect_path': '~/.gemini',
        'description': 'Google Gemini CLI (Antigravity)'
    },
    'copilot': {
        'name': 'GitHub Copilot',
        'user_path': '~/.copilot/skills',
        'detect_path': '~/.copilot',
        'description': 'GitHub Copilot Agent Skills'
    }
}

MARKETPLACE_JSON_TEMPLATE = {
    "name": "",
    "owner": {
        "name": "",
        "email": ""
    },
    "metadata": {
        "description": "",
        "version": "1.0.0"
    },
    "plugins": []
}


def load_config() -> dict:
    """Load existing configuration or return default."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return get_default_config()


def get_default_config() -> dict:
    """Return default configuration for new users."""
    return {
        "platforms": {
            "claude": {"enabled": False, "user_path": "~/.claude/skills", "is_source": False},
            "codex": {"enabled": False, "user_path": "~/.codex/skills", "is_source": False},
            "gemini": {"enabled": False, "user_path": "~/.gemini/skills", "is_source": False},
            "copilot": {"enabled": False, "user_path": "~/.copilot/skills", "is_source": False}
        },
        "sync_mode": "symlink",
        "marketplaces": {
            "private": {"repo": "", "description": "Personal/experimental skills", "visibility": "private"},
            "team": {"repo": "", "description": "Shared skills for collaborators", "visibility": "private"},
            "public": {"repo": "", "description": "Freely available skills", "visibility": "public"}
        },
        "owner": {"name": "", "email": ""},
        "local_repos_path": "~/GitHub"
    }


def save_config(config: dict):
    """Save configuration."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {CONFIG_PATH}")


def get_local_repo_path(config: dict, marketplace: str) -> Path:
    """Get the local clone path for a marketplace repo."""
    base_path = Path(config['local_repos_path']).expanduser()
    repo_url = config['marketplaces'][marketplace].get('repo', '')
    if repo_url:
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return base_path / repo_name
    return base_path / f"skills-{marketplace}"


def detect_platforms() -> dict:
    """Detect which platforms are installed by checking for their config directories."""
    detected = {}
    for platform_id, info in PLATFORMS.items():
        path = Path(info['detect_path']).expanduser()
        detected[platform_id] = path.exists()
    return detected


def get_github_username() -> str:
    """Get the current GitHub username via gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'api', 'user', '-q', '.login'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return ""


def get_github_email() -> str:
    """Get the git config email."""
    try:
        result = subprocess.run(
            ['git', 'config', '--global', 'user.email'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return ""


def get_github_name() -> str:
    """Get the git config name."""
    try:
        result = subprocess.run(
            ['git', 'config', '--global', 'user.name'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return ""


def prompt_with_default(prompt: str, default: str = "") -> str:
    """Prompt for input with a default value."""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    else:
        return input(f"{prompt}: ").strip()


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt for yes/no answer."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ('y', 'yes')


def prompt_choice(prompt: str, options: list, default: str = None) -> str:
    """Prompt user to choose from a list of options."""
    print(prompt)
    for i, option in enumerate(options, 1):
        marker = " (default)" if option == default else ""
        print(f"  {i}. {option}{marker}")

    while True:
        response = input("Enter number or name: ").strip()
        if not response and default:
            return default

        # Check if number
        try:
            idx = int(response)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass

        # Check if name matches
        for option in options:
            if option.lower() == response.lower():
                return option

        print("Invalid choice, try again.")


def create_github_repo(name: str, description: str, visibility: str, org: str = None) -> str:
    """Create a GitHub repository and return its URL."""
    cmd = ['gh', 'repo', 'create']

    if org:
        cmd.append(f"{org}/{name}")
    else:
        cmd.append(name)

    cmd.extend([
        '--description', description,
        f'--{visibility}',
        '--confirm'
    ])

    print(f"Creating repository: {org + '/' if org else ''}{name} ({visibility})")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            if not url.startswith('http'):
                if org:
                    url = f"https://github.com/{org}/{name}"
                else:
                    username = get_github_username()
                    url = f"https://github.com/{username}/{name}"
            print(f"  Created: {url}")
            return url
        else:
            print(f"  Error: {result.stderr}")
            return ""
    except FileNotFoundError:
        print("  Error: gh CLI not found. Please install GitHub CLI.")
        return ""


def init_marketplace_repo(repo_path: Path, marketplace_name: str, config: dict):
    """Initialize a marketplace repository with proper structure."""
    (repo_path / '.claude-plugin').mkdir(parents=True, exist_ok=True)
    (repo_path / 'skills').mkdir(parents=True, exist_ok=True)

    # Get repo name from path or URL
    repo_url = config['marketplaces'][marketplace_name].get('repo', '')
    if repo_url:
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
    else:
        repo_name = f"skills-{marketplace_name}"

    marketplace = MARKETPLACE_JSON_TEMPLATE.copy()
    marketplace['name'] = repo_name
    marketplace['owner'] = config['owner'].copy()
    marketplace['metadata']['description'] = config['marketplaces'][marketplace_name]['description']
    marketplace['plugins'] = [{
        'name': repo_name,
        'description': config['marketplaces'][marketplace_name]['description'],
        'source': './',
        'strict': False,
        'skills': []
    }]

    with open(repo_path / '.claude-plugin' / 'marketplace.json', 'w') as f:
        json.dump(marketplace, f, indent=2)

    readme_content = f"""# Skills Marketplace: {marketplace_name.title()}

{config['marketplaces'][marketplace_name]['description']}

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add <owner>/{repo_name}
```

Then browse and install individual skills via the `/plugin` UI.

## Available Skills

Skills in this marketplace:

| Skill | Description |
|-------|-------------|
| (none yet) | Run `scripts/publish.py <skill> --to {marketplace_name}` to add skills |

## Publishing Skills

To publish a skill to this marketplace:

```bash
~/.claude/skills/skill-manager/scripts/publish.py ~/.claude/skills/my-skill --to {marketplace_name}
```

## Structure

```
{repo_name}/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace configuration
├── skills/
│   └── (your skills here)
└── README.md
```
"""
    with open(repo_path / 'README.md', 'w') as f:
        f.write(readme_content)

    gitignore_content = """.DS_Store
*.pyc
__pycache__/
.env
"""
    with open(repo_path / '.gitignore', 'w') as f:
        f.write(gitignore_content)

    print(f"  Initialized marketplace structure in {repo_path}")


def clone_or_init_repo(url: str, local_path: Path, marketplace_name: str, config: dict) -> bool:
    """Clone an existing repo or initialize a new one."""
    if local_path.exists():
        print(f"  Local repo already exists at {local_path}")
        return True

    local_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ['git', 'clone', url, str(local_path)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"  Cloned to {local_path}")

        marketplace_json = local_path / '.claude-plugin' / 'marketplace.json'
        if not marketplace_json.exists():
            print(f"  Initializing marketplace structure...")
            init_marketplace_repo(local_path, marketplace_name, config)

            subprocess.run(['git', 'add', '.'], cwd=local_path)
            subprocess.run(
                ['git', 'commit', '-m', 'Initialize marketplace structure'],
                cwd=local_path
            )
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=local_path, capture_output=True)
            print(f"  Pushed initial structure to remote")

        return True
    else:
        print(f"  Failed to clone: {result.stderr}")
        return False


def setup_platforms(config: dict) -> dict:
    """Interactive platform setup."""
    print("\n" + "=" * 60)
    print("PLATFORM CONFIGURATION")
    print("=" * 60)

    # Detect installed platforms
    print("\nDetecting installed AI platforms...")
    detected = detect_platforms()

    detected_list = [p for p, found in detected.items() if found]
    not_detected = [p for p, found in detected.items() if not found]

    if detected_list:
        print(f"\n✓ Detected: {', '.join(PLATFORMS[p]['name'] for p in detected_list)}")
    if not_detected:
        print(f"✗ Not detected: {', '.join(PLATFORMS[p]['name'] for p in not_detected)}")

    # Step 1: Choose source platform
    print("\n" + "-" * 40)
    print("STEP 1: Source of Truth")
    print("-" * 40)
    print("\nWhich platform holds your 'source' skills?")
    print("Skills will be synced FROM this platform TO others.")

    # Suggest detected platforms first
    source_options = detected_list + [p for p in not_detected if p not in detected_list]
    default_source = detected_list[0] if detected_list else 'claude'

    for i, platform in enumerate(source_options, 1):
        info = PLATFORMS[platform]
        status = "detected" if detected[platform] else "not detected"
        default_marker = " (recommended)" if platform == default_source else ""
        print(f"  {i}. {info['name']} ({status}){default_marker}")

    while True:
        response = input(f"\nChoose source platform [1-{len(source_options)}]: ").strip()
        if not response:
            source_platform = default_source
            break
        try:
            idx = int(response)
            if 1 <= idx <= len(source_options):
                source_platform = source_options[idx - 1]
                break
        except ValueError:
            pass
        print("Invalid choice, try again.")

    print(f"\nSource platform: {PLATFORMS[source_platform]['name']}")

    # Step 2: Choose target platforms
    print("\n" + "-" * 40)
    print("STEP 2: Sync Targets")
    print("-" * 40)
    print("\nWhich platforms should receive synced skills?")
    print("(Skills from your source will be copied/symlinked here)")

    target_platforms = []
    for platform in PLATFORMS:
        if platform == source_platform:
            continue
        info = PLATFORMS[platform]
        status = "detected" if detected[platform] else "not detected"
        default_enable = detected[platform]

        enable = prompt_yes_no(f"  Sync to {info['name']} ({status})?", default_enable)
        if enable:
            target_platforms.append(platform)

    if not target_platforms:
        print("\nNo sync targets selected. You can add them later by re-running init.")
    else:
        print(f"\nWill sync to: {', '.join(PLATFORMS[p]['name'] for p in target_platforms)}")

    # Step 3: Sync mode
    print("\n" + "-" * 40)
    print("STEP 3: Sync Mode")
    print("-" * 40)
    print("\nHow should skills be synced to target platforms?")
    print("  1. symlink - Create symbolic links (changes propagate automatically)")
    print("  2. copy - Copy files (independent copies, must re-sync to update)")

    current_mode = config.get('sync_mode', 'symlink')
    mode_response = prompt_with_default("Sync mode", current_mode)
    sync_mode = mode_response if mode_response in ('symlink', 'copy') else 'symlink'

    # Update config
    for platform in PLATFORMS:
        if platform not in config.get('platforms', {}):
            config.setdefault('platforms', {})[platform] = {
                "enabled": False,
                "user_path": PLATFORMS[platform]['user_path'],
                "is_source": False
            }

        config['platforms'][platform]['is_source'] = (platform == source_platform)
        config['platforms'][platform]['enabled'] = (
            platform == source_platform or platform in target_platforms
        )

    config['sync_mode'] = sync_mode

    return config


def setup_marketplaces(config: dict, args) -> dict:
    """Interactive marketplace setup."""
    print("\n" + "=" * 60)
    print("MARKETPLACE CONFIGURATION")
    print("=" * 60)
    print("\nMarketplaces let you publish and share skills via GitHub repos.")
    print("You can create as many marketplaces as you need (e.g., private, team, project-specific).")

    # Step 1: Owner info
    print("\n" + "-" * 40)
    print("STEP 1: Owner Information")
    print("-" * 40)

    default_name = config['owner'].get('name') or get_github_name()
    default_email = config['owner'].get('email') or get_github_email()

    config['owner']['name'] = prompt_with_default("Your name", default_name)
    config['owner']['email'] = prompt_with_default("Your email", default_email)

    # Step 2: GitHub username/org
    print("\n" + "-" * 40)
    print("STEP 2: Repository Configuration")
    print("-" * 40)

    github_username = get_github_username()
    if not github_username:
        github_username = input("GitHub username: ").strip()

    default_org = args.org or github_username

    # Step 3: Configure marketplaces
    print("\n" + "-" * 40)
    print("STEP 3: Marketplace Repositories")
    print("-" * 40)

    # Show existing marketplaces
    existing_marketplaces = list(config.get('marketplaces', {}).keys())
    if existing_marketplaces:
        print(f"\nExisting marketplaces: {', '.join(existing_marketplaces)}")

    # Configure existing marketplaces
    for mkt_name, mkt_config in list(config.get('marketplaces', {}).items()):
        existing_url = mkt_config.get('repo', '')
        default_url = existing_url or f"https://github.com/{default_org}/skills-{mkt_name}"

        print(f"\n{mkt_name.upper()}:")
        url = prompt_with_default(f"  Repository URL (blank to skip)", default_url)
        config['marketplaces'][mkt_name]['repo'] = url

    # Option to add new marketplaces
    while True:
        add_more = prompt_yes_no("\nAdd a new custom marketplace?", False)
        if not add_more:
            break

        new_name = input("  Marketplace name (e.g., 'myproject'): ").strip().lower()
        if not new_name:
            continue
        if new_name in config['marketplaces']:
            print(f"  Marketplace '{new_name}' already exists.")
            continue

        new_desc = prompt_with_default(f"  Description", f"Skills for {new_name}")
        new_visibility = prompt_choice("  Visibility:", ['private', 'public'], 'private')
        new_url = prompt_with_default(f"  Repository URL", f"https://github.com/{github_username}/skills-{new_name}")

        config['marketplaces'][new_name] = {
            'repo': new_url,
            'description': new_desc,
            'visibility': new_visibility
        }
        print(f"  Added marketplace: {new_name}")

    # Step 4: Local repos path
    print("\n" + "-" * 40)
    print("STEP 4: Local Configuration")
    print("-" * 40)

    default_local_path = config.get('local_repos_path', '~/GitHub')
    config['local_repos_path'] = prompt_with_default("Local repos directory", default_local_path)

    # Save config before repo operations
    save_config(config)

    # Step 5: Create/clone repositories
    print("\n" + "-" * 40)
    print("STEP 5: Repository Setup")
    print("-" * 40)

    # Check if gh CLI is available
    gh_available = False
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
        gh_available = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("\nNote: GitHub CLI (gh) not found.")
        print("You can install it with: brew install gh")
        print("Without gh, you'll need to create repos manually on GitHub.\n")

    create_repos = False
    if gh_available and not args.skip_create:
        create_repos = prompt_yes_no("\nCreate GitHub repositories that don't exist?", True)

    for mkt_name, mkt_config in config['marketplaces'].items():
        print(f"\n{mkt_name.upper()}:")
        url = mkt_config.get('repo', '')

        if not url:
            print("  Skipped (no URL configured)")
            continue

        if create_repos and gh_available:
            repo_name = url.split('/')[-1]
            repo_owner = url.split('/')[-2]

            check_result = subprocess.run(
                ['gh', 'repo', 'view', f"{repo_owner}/{repo_name}"],
                capture_output=True,
                text=True
            )

            if check_result.returncode != 0:
                visibility = mkt_config.get('visibility', 'private')
                description = mkt_config.get('description', f'Skills marketplace: {mkt_name}')
                created_url = create_github_repo(
                    repo_name,
                    description,
                    visibility,
                    org=repo_owner if repo_owner != github_username else None
                )
                if created_url:
                    config['marketplaces'][mkt_name]['repo'] = created_url
                    url = created_url
            else:
                print(f"  Repository already exists: {url}")

        # Clone/init local copy
        local_path = get_local_repo_path(config, mkt_name)
        clone_or_init_repo(url, local_path, mkt_name, config)

    return config


def main():
    parser = argparse.ArgumentParser(description='Set up skill-manager for multi-platform sync and marketplaces')
    parser.add_argument('--skip-create', action='store_true',
                        help='Skip creating new GitHub repos')
    parser.add_argument('--skip-marketplaces', action='store_true',
                        help='Skip marketplace setup (only configure platforms)')
    parser.add_argument('--org',
                        help='GitHub organization for team/public repos')

    args = parser.parse_args()

    print("=" * 60)
    print("SKILL MANAGER SETUP")
    print("=" * 60)
    print("\nThis wizard will configure skill-manager for your environment.")
    print("You can re-run this anytime to change settings.\n")

    # Load existing config
    config = load_config()

    # Platform setup
    config = setup_platforms(config)
    save_config(config)

    # Marketplace setup (optional)
    if not args.skip_marketplaces:
        setup_mkt = prompt_yes_no("\nWould you like to set up marketplace repositories for skill distribution?", True)
        if setup_mkt:
            config = setup_marketplaces(config, args)
            save_config(config)

    # Final summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)

    # Platform summary
    print("\nPlatform Configuration:")
    source_platform = None
    target_platforms = []
    for platform, pconfig in config.get('platforms', {}).items():
        if pconfig.get('is_source'):
            source_platform = platform
        elif pconfig.get('enabled'):
            target_platforms.append(platform)

    if source_platform:
        print(f"  Source: {PLATFORMS[source_platform]['name']}")
    if target_platforms:
        print(f"  Sync to: {', '.join(PLATFORMS[p]['name'] for p in target_platforms)}")
    print(f"  Sync mode: {config.get('sync_mode', 'symlink')}")

    # Marketplace summary
    configured_marketplaces = [
        (name, mkt.get('repo'))
        for name, mkt in config.get('marketplaces', {}).items()
        if mkt.get('repo')
    ]

    if configured_marketplaces:
        print("\nMarketplace Configuration:")
        for name, url in configured_marketplaces:
            print(f"  {name}: {url}")
        print(f"\nLocal repos: {config['local_repos_path']}")

    # Next steps
    print("\n" + "-" * 60)
    print("NEXT STEPS:")
    print("-" * 60)

    if source_platform and target_platforms:
        print("\n1. Sync a skill to other platforms:")
        print(f"   scripts/sync.py ~/.{source_platform}/skills/my-skill --to {','.join(target_platforms)}")

    if configured_marketplaces:
        first_marketplace = configured_marketplaces[0][0]
        print("\n2. Publish a skill to a marketplace:")
        print(f"   scripts/publish.py ~/.claude/skills/my-skill --to {first_marketplace}")
        print("\n3. Add marketplaces to Claude Code:")
        for name, url in configured_marketplaces:
            owner_repo = '/'.join(url.split('/')[-2:])
            print(f"   /plugin marketplace add {owner_repo}")

    print("-" * 60)


if __name__ == '__main__':
    main()
