#!/usr/bin/env python3
"""
Skill Validator - Validate skills against the Agent Skills specification.

Usage:
    validate.py <skill-path>
    validate.py <skill-path> --strict
    validate.py <skill-path> --format json

Options:
    --strict           Enable strict validation (warnings become errors)
    --format FORMAT    Output format: text, json (default: text)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


# Validation constants from Agent Skills spec
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
ALLOWED_FRONTMATTER_FIELDS = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}
NAME_PATTERN = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def add_info(self, message: str):
        self.info.append(message)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
        }


def parse_yaml_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from SKILL.md content."""
    if not content.startswith('---'):
        return None, "No YAML frontmatter found (must start with ---)"

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None, "Invalid frontmatter format (missing closing ---)"

    # Simple YAML parsing
    frontmatter = {}
    current_key = None
    multiline_value = []

    for line in match.group(1).split('\n'):
        # Skip empty lines
        if not line.strip():
            continue

        # Check for new key
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            # Save previous multiline value
            if current_key and multiline_value:
                frontmatter[current_key] = '\n'.join(multiline_value)
                multiline_value = []

            key, value = line.split(':', 1)
            current_key = key.strip()
            value = value.strip()

            # Handle inline value
            if value:
                # Remove quotes
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                frontmatter[current_key] = value
            else:
                multiline_value = []
        elif current_key:
            # Multiline value continuation
            multiline_value.append(line.strip())

    # Handle final multiline value
    if current_key and multiline_value:
        frontmatter[current_key] = '\n'.join(multiline_value)

    return frontmatter, None


def validate_skill(skill_path: Path, strict: bool = False) -> ValidationResult:
    """Validate a skill directory against the Agent Skills specification."""
    result = ValidationResult()

    # Check directory exists
    if not skill_path.exists():
        result.add_error(f"Path does not exist: {skill_path}")
        return result

    if not skill_path.is_dir():
        result.add_error(f"Path is not a directory: {skill_path}")
        return result

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        result.add_error("SKILL.md not found (required)")
        return result

    # Read and parse SKILL.md
    try:
        content = skill_md.read_text()
    except Exception as e:
        result.add_error(f"Cannot read SKILL.md: {e}")
        return result

    # Parse frontmatter
    frontmatter, parse_error = parse_yaml_frontmatter(content)
    if parse_error:
        result.add_error(parse_error)
        return result

    # Check for unexpected fields
    unexpected = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_FIELDS
    if unexpected:
        result.add_error(f"Unexpected frontmatter fields: {', '.join(sorted(unexpected))}")

    # Validate name field
    if 'name' not in frontmatter:
        result.add_error("Missing required field: name")
    else:
        name = frontmatter['name']
        if not isinstance(name, str) or not name:
            result.add_error("Field 'name' must be a non-empty string")
        else:
            # Check length
            if len(name) > MAX_NAME_LENGTH:
                result.add_error(f"Name too long: {len(name)} chars (max {MAX_NAME_LENGTH})")

            # Check format
            if not NAME_PATTERN.match(name):
                result.add_error(f"Invalid name format: '{name}'. Must be lowercase letters, digits, and hyphens only. "
                               "Cannot start/end with hyphen or have consecutive hyphens.")

            # Check name matches directory
            if name != skill_path.name:
                result.add_warning(f"Name '{name}' does not match directory name '{skill_path.name}'. "
                                 "Spec recommends they match.")

    # Validate description field
    if 'description' not in frontmatter:
        result.add_error("Missing required field: description")
    else:
        description = frontmatter['description']
        if not isinstance(description, str) or not description:
            result.add_error("Field 'description' must be a non-empty string")
        else:
            # Check length
            if len(description) > MAX_DESCRIPTION_LENGTH:
                result.add_error(f"Description too long: {len(description)} chars (max {MAX_DESCRIPTION_LENGTH})")

            # Check for angle brackets
            if '<' in description or '>' in description:
                result.add_error("Description cannot contain angle brackets (< or >)")

            # Check for quality (warnings)
            if len(description) < 50:
                result.add_warning("Description is very short. Consider adding more detail about WHAT and WHEN.")

            if not any(word in description.lower() for word in ['use when', 'when', 'for', 'help']):
                result.add_warning("Description should explain WHEN to use this skill, not just WHAT it does.")

    # Validate optional fields
    if 'compatibility' in frontmatter:
        compat = frontmatter['compatibility']
        if len(str(compat)) > MAX_COMPATIBILITY_LENGTH:
            result.add_error(f"Compatibility field too long: {len(str(compat))} chars (max {MAX_COMPATIBILITY_LENGTH})")

    # Check body content
    body_start = content.find('---', 3)
    if body_start != -1:
        body = content[body_start + 3:].strip()
        if not body:
            result.add_warning("SKILL.md body is empty. Consider adding instructions.")
        elif len(body.split('\n')) > 500:
            result.add_warning("SKILL.md body exceeds 500 lines. Consider moving content to references/ files.")

    # Check directory structure
    scripts_dir = skill_path / 'scripts'
    references_dir = skill_path / 'references'
    assets_dir = skill_path / 'assets'

    if scripts_dir.exists():
        result.add_info(f"scripts/ directory found with {len(list(scripts_dir.iterdir()))} files")
    if references_dir.exists():
        result.add_info(f"references/ directory found with {len(list(references_dir.iterdir()))} files")
    if assets_dir.exists():
        result.add_info(f"assets/ directory found with {len(list(assets_dir.iterdir()))} files")

    # Check for common anti-patterns
    for unwanted in ['README.md', 'CHANGELOG.md', 'INSTALLATION.md']:
        if (skill_path / unwanted).exists():
            result.add_warning(f"Found {unwanted} - skills should only contain SKILL.md and resource directories")

    # In strict mode, warnings become errors
    if strict:
        result.errors.extend(result.warnings)
        result.warnings = []

    return result


def format_text_output(skill_path: Path, result: ValidationResult) -> str:
    """Format validation result as text."""
    lines = []
    lines.append(f"Validating: {skill_path}")
    lines.append("=" * 60)

    if result.valid:
        lines.append("VALID")
    else:
        lines.append("INVALID")

    if result.errors:
        lines.append("\nErrors:")
        for error in result.errors:
            lines.append(f"  [E] {error}")

    if result.warnings:
        lines.append("\nWarnings:")
        for warning in result.warnings:
            lines.append(f"  [W] {warning}")

    if result.info:
        lines.append("\nInfo:")
        for info in result.info:
            lines.append(f"  [I] {info}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Validate skills against Agent Skills specification')
    parser.add_argument('skill_path', type=Path,
                        help='Path to skill directory to validate')
    parser.add_argument('--strict', action='store_true',
                        help='Treat warnings as errors')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                        help='Output format')

    args = parser.parse_args()

    skill_path = args.skill_path.resolve()
    result = validate_skill(skill_path, args.strict)

    if args.format == 'json':
        output = result.to_dict()
        output['skill_path'] = str(skill_path)
        print(json.dumps(output, indent=2))
    else:
        print(format_text_output(skill_path, result))

    sys.exit(0 if result.valid else 1)


if __name__ == '__main__':
    main()
