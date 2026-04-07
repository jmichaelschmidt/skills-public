#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install_starter_pack.sh --target /path/to/repo [--profile generic-v2] [--install|--refresh] [--force] [--dry-run]

Copies the reusable starter-pack templates into a target repository.

Profiles:
- generic-v2      : repo-independent starter-pack (default)

Modes:
- --install  : non-destructive install; skips existing managed files (default)
- --refresh  : overwrite managed starter-pack files from the canonical templates
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET=""
FORCE=0
DRY_RUN=0
MODE="install"
PROFILE="generic-v2"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --install)
      MODE="install"
      shift
      ;;
    --refresh)
      MODE="refresh"
      FORCE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${TARGET}" ]]; then
  echo "--target is required" >&2
  usage >&2
  exit 1
fi

case "${PROFILE}" in
  generic-v2)
    TEMPLATE_ROOT="${SKILL_DIR}/templates"
    declare -a SOURCES=(
      "AGENTS.md:AGENTS.md"
      ".codex/config.toml:.codex/config.toml"
      ".codex/agents:.codex/agents"
      ".claude/agents:.claude/agents"
      "docs/starter-pack:docs/starter-pack"
      "tools/starter-pack:tools/starter-pack"
    )
    ;;
  *)
    echo "Unknown profile: ${PROFILE}" >&2
    usage >&2
    exit 1
    ;;
esac

copy_item() {
  local source="$1"
  local destination="$2"
  local action="INSTALLED"

  if [[ "${MODE}" == "refresh" ]]; then
    action="REFRESHED"
  fi

  if [[ -e "${destination}" && "${FORCE}" -ne 1 ]]; then
    echo "SKIP ${destination} (managed starter-pack file exists; rerun with --refresh to replace from canonical templates)"
    return 0
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "DRY-RUN ${action} ${destination} <= ${source}"
    return 0
  fi

  mkdir -p "$(dirname "${destination}")"
  if [[ -d "${source}" ]]; then
    rm -rf "${destination}"
    cp -R "${source}" "${destination}"
  else
    cp "${source}" "${destination}"
  fi
  echo "${action} ${destination}"
}

for mapping in "${SOURCES[@]}"; do
  source_rel="${mapping%%:*}"
  destination_rel="${mapping#*:}"
  copy_item "${TEMPLATE_ROOT}/${source_rel}" "${TARGET}/${destination_rel}"
done

echo "Starter-pack template ${MODE} complete for ${PROFILE}."
