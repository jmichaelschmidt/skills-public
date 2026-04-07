#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

MISSING_DEPENDENCIES: list[str] = []

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]
        MISSING_DEPENDENCIES.append("tomli (or Python 3.11+ for stdlib tomllib)")

try:
    import yaml
except ModuleNotFoundError:
    yaml = None  # type: ignore[assignment]
    MISSING_DEPENDENCIES.append("PyYAML")


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_CLAUDE_HOME = Path.home() / ".claude"
STARTER_PACK_SKILL_NAME = "subagent-starter-pack"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
IGNORED_NAMES = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc"}
REQUIRED_DOCS = [
    "docs/starter-pack/workflow.md",
    "docs/starter-pack/operator-brief.md",
    "docs/starter-pack/artifact-workflows.md",
    "docs/starter-pack/setup.md",
    "docs/starter-pack/repo-hygiene-policy.md",
    "docs/starter-pack/security-review-policy.md",
]
MANAGED_TEMPLATE_MAPPINGS = [
    ("AGENTS.md", "AGENTS.md"),
    (".codex/config.toml", ".codex/config.toml"),
    (".codex/agents", ".codex/agents"),
    (".claude/agents", ".claude/agents"),
    ("docs/starter-pack", "docs/starter-pack"),
    ("tools/starter-pack", "tools/starter-pack"),
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generic starter-pack files for a repo.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME)
    parser.add_argument("--claude-home", type=Path, default=DEFAULT_CLAUDE_HOME)
    parser.add_argument(
        "--starter-pack-skill-dir",
        type=Path,
        default=None,
        help="Path to a local subagent-starter-pack skill checkout to validate against instead of the installed machine copy.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def load_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:  # pragma: no cover
        raise RuntimeError("Missing TOML parser dependency.")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"TOML root must be an object: {path}")
    return data


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    if yaml is None:  # pragma: no cover
        raise RuntimeError("Missing YAML parser dependency.")
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Missing YAML frontmatter: {path}")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"Frontmatter must decode to an object: {path}")
    body = text[match.end() :].strip()
    return data, body


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_NAMES for part in path.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def resolve_starter_pack_skill_dir(
    codex_home: Path,
    claude_home: Path,
    explicit_skill_dir: Path | None,
) -> tuple[Path | None, Path | None, list[CheckResult]]:
    checks: list[CheckResult] = []
    candidates: list[Path] = []
    if explicit_skill_dir is not None:
        candidates.append(explicit_skill_dir.expanduser())
    candidates.extend(
        [
            codex_home / "skills" / STARTER_PACK_SKILL_NAME,
            claude_home / "skills" / STARTER_PACK_SKILL_NAME,
        ]
    )
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve() if candidate.exists() else candidate
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            checks.append(CheckResult(name="starter_pack:skill_dir_present", ok=True, detail=str(candidate)))
            template_root = candidate / "templates"
            checks.append(
                CheckResult(
                    name="starter_pack:template_root_present",
                    ok=template_root.is_dir(),
                    detail=str(template_root),
                )
            )
            if template_root.is_dir():
                return candidate, template_root, checks
            return candidate, None, checks
    checks.append(
        CheckResult(
            name="starter_pack:skill_dir_present",
            ok=False,
            detail=" | ".join(str(path) for path in candidates),
        )
    )
    return None, None, checks


def validate_repo_docs(repo_root: Path) -> list[CheckResult]:
    return [CheckResult(name=f"doc:{rel_path}", ok=(repo_root / rel_path).exists(), detail=str(repo_root / rel_path)) for rel_path in REQUIRED_DOCS]


def validate_managed_files(repo_root: Path, template_root: Path | None) -> list[CheckResult]:
    checks: list[CheckResult] = []
    if template_root is None:
        return checks
    for template_rel, repo_rel in MANAGED_TEMPLATE_MAPPINGS:
        template_path = template_root / template_rel
        repo_path = repo_root / repo_rel
        checks.append(CheckResult(name=f"starter_pack:{repo_rel}:template_exists", ok=template_path.exists(), detail=str(template_path)))
        if not template_path.exists():
            continue
        if template_path.is_dir():
            expected_files = [path.relative_to(template_path) for path in iter_files(template_path)]
            actual_files = [path.relative_to(repo_path) for path in iter_files(repo_path)] if repo_path.is_dir() else []
            missing_files = [str(path) for path in expected_files if path not in actual_files]
            extra_files = [str(path) for path in actual_files if path not in expected_files]
            checks.append(
                CheckResult(
                    name=f"starter_pack:{repo_rel}:file_set_matches",
                    ok=not missing_files and not extra_files,
                    detail=f"missing={missing_files or ['-']} extra={extra_files or ['-']}",
                )
            )
            for relative_path in expected_files:
                template_file = template_path / relative_path
                repo_file = repo_path / relative_path
                matches = repo_file.exists() and sha256(template_file) == sha256(repo_file)
                detail = f"repo={repo_file} canonical={template_file}"
                if repo_file.exists():
                    detail += f" repo_sha256={sha256(repo_file)} canonical_sha256={sha256(template_file)}"
                checks.append(
                    CheckResult(
                        name=f"starter_pack:{repo_rel}/{relative_path}:matches_canonical",
                        ok=matches,
                        detail=detail,
                    )
                )
        else:
            matches = repo_path.exists() and sha256(template_path) == sha256(repo_path)
            detail = f"repo={repo_path} canonical={template_path}"
            if repo_path.exists():
                detail += f" repo_sha256={sha256(repo_path)} canonical_sha256={sha256(template_path)}"
            checks.append(CheckResult(name=f"starter_pack:{repo_rel}:matches_canonical", ok=matches, detail=detail))
    return checks


def validate_codex_config(repo_root: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    config_path = repo_root / ".codex" / "config.toml"
    if not config_path.exists():
        return [CheckResult(name="codex:config_exists", ok=False, detail=str(config_path))]
    try:
        data = load_toml(config_path)
    except Exception as exc:
        return [CheckResult(name="codex:config_parse", ok=False, detail=str(exc))]
    agents = data.get("agents")
    checks.append(CheckResult(name="codex:config_parse", ok=True, detail=str(config_path)))
    checks.append(CheckResult(name="codex:agents_table_present", ok=isinstance(agents, dict), detail="expected [agents] table"))
    return checks


def validate_codex_agents(repo_root: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    agents_dir = repo_root / ".codex" / "agents"
    files = sorted(agents_dir.glob("*.toml"))
    checks.append(CheckResult(name="codex:agents_present", ok=bool(files), detail=f"count={len(files)}"))
    for path in files:
        try:
            data = load_toml(path)
        except Exception as exc:
            checks.append(CheckResult(name=f"codex:{path.name}:parse", ok=False, detail=str(exc)))
            continue
        for field in ("name", "description", "developer_instructions"):
            checks.append(CheckResult(name=f"codex:{path.name}:{field}", ok=bool(data.get(field)), detail=repr(data.get(field))))
    return checks


def validate_claude_agents(repo_root: Path, claude_home: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    agents_dir = repo_root / ".claude" / "agents"
    files = sorted(agents_dir.glob("*.md"))
    checks.append(CheckResult(name="claude:agents_present", ok=bool(files), detail=f"count={len(files)}"))
    for path in files:
        try:
            frontmatter, body = parse_frontmatter(path)
        except Exception as exc:
            checks.append(CheckResult(name=f"claude:{path.name}:parse", ok=False, detail=str(exc)))
            continue
        for field in ("name", "description"):
            checks.append(CheckResult(name=f"claude:{path.name}:{field}", ok=bool(frontmatter.get(field)), detail=repr(frontmatter.get(field))))
        checks.append(CheckResult(name=f"claude:{path.name}:body", ok=bool(body), detail="non-empty body required"))
        skills = frontmatter.get("skills") or []
        if isinstance(skills, str):
            skills = [skills]
        if not isinstance(skills, list):
            checks.append(CheckResult(name=f"claude:{path.name}:skills", ok=False, detail="skills must be a list or string"))
            continue
        for skill in skills:
            skill_path = claude_home / "skills" / str(skill) / "SKILL.md"
            checks.append(CheckResult(name=f"claude:{path.name}:skill:{skill}", ok=skill_path.exists(), detail=str(skill_path)))
    return checks


def collect_checks(
    repo_root: Path,
    codex_home: Path,
    claude_home: Path,
    starter_pack_skill_dir: Path | None = None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(validate_repo_docs(repo_root))
    _, template_root, skill_checks = resolve_starter_pack_skill_dir(codex_home, claude_home, starter_pack_skill_dir)
    checks.extend(skill_checks)
    checks.extend(validate_managed_files(repo_root, template_root))
    checks.extend(validate_codex_config(repo_root))
    checks.extend(validate_codex_agents(repo_root))
    checks.extend(validate_claude_agents(repo_root, claude_home))
    return checks


def main() -> int:
    args = parse_args()
    if MISSING_DEPENDENCIES:
        detail = "Missing validation dependencies: " + ", ".join(MISSING_DEPENDENCIES)
        if args.json:
            json.dump({"ok": False, "checks": [], "error": detail}, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            print(detail)
            print("Run: ./tools/starter-pack/bootstrap_env.sh")
        return 1
    checks = collect_checks(
        args.repo_root.resolve(),
        args.codex_home.resolve(),
        args.claude_home.resolve(),
        args.starter_pack_skill_dir.resolve() if args.starter_pack_skill_dir is not None else None,
    )
    failed = [check for check in checks if not check.ok]
    if args.json:
        json.dump({"ok": not failed, "checks": [asdict(check) for check in checks]}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for check in checks:
            prefix = "OK" if check.ok else "FAIL"
            print(f"[{prefix}] {check.name}: {check.detail}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
