#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "== GameUIAgent Loops Bootstrap =="
echo "Repository: $REPO_ROOT"
echo

echo "Read first:"
echo "  - docs/loops/README.md"
echo "  - docs/loops/required-skills.md"
echo "  - docs/loops/project-workflow.md"
echo "  - docs/loops/skill-installation.md"
echo

echo "Core project docs:"
echo "  - docs/README.md"
echo "  - docs/product/prd.md"
echo "  - docs/product/feature-map.md"
echo "  - docs/tasks/implementation-roadmap.md"
echo

bash "$SCRIPT_DIR/check-skills.sh"

echo
echo "Recommended next action:"
echo "  Pick the current project phase in docs/loops/project-workflow.md, then activate the listed skills before implementation."
