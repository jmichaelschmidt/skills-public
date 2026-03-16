#!/usr/bin/env python3
"""Script-level regression tests for skill-manager hardening."""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent
SKILL_MANAGER_ROOT = TEST_ROOT.parent
SCRIPTS_DIR = SKILL_MANAGER_ROOT / 'scripts'


def load_script_module(script_name: str):
    """Load a script module by file name."""
    module_name = script_name.replace('-', '_').replace('.py', '')
    module_path = SCRIPTS_DIR / script_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd: list, cwd: Path = None):
    """Run shell command and return completed process."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


class InventoryCompatibilityTests(unittest.TestCase):
    def test_include_marketplace_legacy_forms_normalize(self):
        inventory = load_script_module('inventory.py')

        cases = [
            (['--include', 'marketplace'], ['--include-marketplace']),
            (['--include=marketplace'], ['--include-marketplace']),
            (['--include-marketplace'], ['--include-marketplace']),
        ]

        for args, expected in cases:
            with self.subTest(args=args):
                normalized = inventory.normalize_legacy_args(args)
                self.assertEqual(normalized, expected)


class MarketplaceGeneralizationTests(unittest.TestCase):
    def test_local_repo_path_uses_repo_name_when_available(self):
        publish = load_script_module('publish.py')
        config = {
            'local_repos_path': '/tmp/skills-test',
            'marketplaces': {
                'partner': {'repo': 'https://github.com/example-org/partner-skills.git'}
            },
        }
        path = publish.get_local_repo_path(config, 'partner')
        self.assertEqual(path, Path('/tmp/skills-test/partner-skills'))

    def test_local_repo_path_falls_back_to_marketplace_key(self):
        publish = load_script_module('publish.py')
        config = {
            'local_repos_path': '/tmp/skills-test',
            'marketplaces': {
                'enterprise-core': {'repo': ''}
            },
        }
        path = publish.get_local_repo_path(config, 'enterprise-core')
        self.assertEqual(path, Path('/tmp/skills-test/enterprise-core'))


class BranchDetectionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix='skill-manager-tests-'))
        self.remote = self.tempdir / 'remote.git'
        self.seed = self.tempdir / 'seed'
        self.clone = self.tempdir / 'clone'

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _init_repo_with_default_branch(self, branch_name: str):
        run(['git', 'init', '--bare', str(self.remote)])
        run(['git', 'init', str(self.seed)])
        run(['git', 'config', 'user.name', 'Test User'], cwd=self.seed)
        run(['git', 'config', 'user.email', 'test@example.com'], cwd=self.seed)

        (self.seed / 'README.md').write_text('seed\n')
        run(['git', 'add', '.'], cwd=self.seed)
        run(['git', 'commit', '-m', 'seed'], cwd=self.seed)
        run(['git', 'branch', '-M', branch_name], cwd=self.seed)
        run(['git', 'remote', 'add', 'origin', str(self.remote)], cwd=self.seed)
        run(['git', 'push', '-u', 'origin', branch_name], cwd=self.seed)
        run(['git', '--git-dir', str(self.remote), 'symbolic-ref', 'HEAD', f'refs/heads/{branch_name}'])
        run(['git', 'clone', str(self.remote), str(self.clone)])

    def test_detect_default_branch_from_origin_head(self):
        publish = load_script_module('publish.py')
        self._init_repo_with_default_branch('trunk')
        detected = publish.detect_default_branch(self.clone)
        self.assertEqual(detected, 'trunk')


class DryRunOutputTests(unittest.TestCase):
    def test_mirror_plan_format_is_deterministic(self):
        mirror = load_script_module('marketplace-mirror.py')
        plan = mirror.format_mirror_plan(
            source_marketplace='public',
            target_marketplace='partner',
            source_ref='v1.2.0',
            source_commit='abc1234',
            base_branch='main',
            selected_skills=['engineering-scope', 'skill-manager'],
        )

        expected = (
            "======================================================================\n"
            "MARKETPLACE MIRROR\n"
            "======================================================================\n"
            "Source: public @ v1.2.0 (abc1234)\n"
            "Target: partner\n"
            "Base branch: main\n"
            "Skills: engineering-scope, skill-manager"
        )
        self.assertEqual(plan, expected)


if __name__ == '__main__':
    unittest.main()
