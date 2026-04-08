#!/usr/bin/env python3
"""Workspace validation regression tests."""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
import sys


TEST_ROOT = Path(__file__).resolve().parent


def find_workspace_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "scripts" / "validate_workspace.py").exists():
            return candidate
    return None


WORKSPACE_ROOT = find_workspace_root(TEST_ROOT)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class WorkspaceValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="workspace-validation-tests-"))
        if WORKSPACE_ROOT is None:
            self.skipTest("workspace validator not present in this checkout")
        self.workspace_validator = load_module(
            WORKSPACE_ROOT / "scripts" / "validate_workspace.py",
            "workspace_validator",
        )
        self.skill_validator = load_module(
            WORKSPACE_ROOT / "skills-public" / "skills" / "skill-manager" / "scripts" / "validate.py",
            "skill_validator",
        )
        self.starter_pack_validator = load_module(
            WORKSPACE_ROOT
            / "skills-public"
            / "skills"
            / "subagent-starter-pack"
            / "templates"
            / "tools"
            / "starter-pack"
            / "validate.py",
            "starter_pack_validator",
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_collect_skill_checks_reports_missing_frontmatter(self):
        skill_dir = self.tempdir / "skills-team" / "skills" / "demo-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Demo Skill\n", encoding="utf-8")

        checks = self.workspace_validator.collect_skill_checks(
            self.tempdir,
            validator_module=self.skill_validator,
        )

        self.assertEqual(len(checks), 1)
        self.assertFalse(checks[0].ok)
        self.assertIn("No YAML frontmatter found", checks[0].detail)

    def test_missing_workspace_secrets_patterns_is_reported(self):
        check = self.workspace_validator.check_secrets_patterns_file(self.tempdir)

        self.assertFalse(check.ok)
        self.assertTrue(check.detail.endswith(".secrets-patterns"))

    def test_invalid_starter_pack_codex_metadata_is_detected(self):
        agents_dir = self.tempdir / ".codex" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "planner.toml").write_text('name = "planner"\n', encoding="utf-8")

        checks = self.starter_pack_validator.validate_codex_agents(self.tempdir)

        failed_checks = {check.name: check for check in checks if not check.ok}
        self.assertIn("codex:planner.toml:description", failed_checks)


if __name__ == "__main__":
    unittest.main()
