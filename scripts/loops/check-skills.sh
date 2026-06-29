#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$SCRIPT_DIR/skills.manifest.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: missing skills manifest: $MANIFEST" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required to read $MANIFEST" >&2
  exit 1
fi

export LOOPS_REPO_ROOT="$REPO_ROOT"
export LOOPS_MANIFEST="$MANIFEST"

python3 <<'PY'
import json
import os
from pathlib import Path

repo_root = Path(os.environ["LOOPS_REPO_ROOT"])
manifest_path = Path(os.environ["LOOPS_MANIFEST"])
manifest = json.loads(manifest_path.read_text())

raw_paths = manifest.get("skillSearchPaths", [])
search_paths = []
for raw in raw_paths:
    expanded = raw.replace("$HOME", str(Path.home()))
    path = Path(expanded)
    if not path.is_absolute():
        path = repo_root / path
    search_paths.append(path)

def find_skill(skill_id: str):
    candidates = [
        skill_id,
        skill_id.replace("-", "_"),
        skill_id.replace("_", "-"),
    ]
    for base in search_paths:
        if not base.exists():
            continue
        for name in candidates:
            for path in (base / name, base / f"{name}.md"):
                if path.exists():
                    return path
    return None

installed = []
missing_required = []
required_custom = []
recommended_missing = []
optional_missing = []

for skill in manifest.get("skills", []):
    skill_id = skill["id"]
    declared_status = skill.get("status", "")
    found = find_skill(skill_id)
    row = {
        "id": skill_id,
        "name": skill.get("name", skill_id),
        "category": skill.get("category", "uncategorized"),
        "required": bool(skill.get("required")),
        "declared_status": declared_status,
        "fallback": skill.get("fallback"),
        "path": str(found) if found else None,
    }

    if found:
        installed.append(row)
    elif declared_status == "required-custom":
        required_custom.append(row)
    elif row["required"]:
        missing_required.append(row)
    elif declared_status == "optional":
        optional_missing.append(row)
    else:
        recommended_missing.append(row)

print("== GameUIAgent Loops Skill Check ==")
print(f"Manifest: {manifest_path}")
print("Search paths:")
for path in search_paths:
    marker = "exists" if path.exists() else "missing"
    print(f"  - {path} [{marker}]")

def print_group(title, rows):
    print(f"\n{title} ({len(rows)})")
    if not rows:
        print("  - none")
        return
    for row in rows:
        suffix = f" -> {row['path']}" if row.get("path") else ""
        fallback = f", fallback: {row['fallback']}" if row.get("fallback") else ""
        print(f"  - {row['id']} [{row['category']}]{fallback}{suffix}")

print_group("Installed / detected", installed)
print_group("Required custom skills to create", required_custom)
print_group("Missing required built-in skills", missing_required)
print_group("Recommended skills not detected", recommended_missing)
print_group("Optional skills not detected", optional_missing)

if required_custom:
    print("\nNext step for required custom skills:")
    print("  Use the Trae skill-creator flow to create these project-specific skills when implementation begins.")

if missing_required:
    print("\nERROR: required built-in skills are missing.")
    raise SystemExit(2)

print("\nSkill check completed.")
PY
