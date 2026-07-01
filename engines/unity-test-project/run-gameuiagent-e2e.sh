#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${UNITY_EDITOR_EXECUTABLE:-}" ]]; then
  echo "UNITY_EDITOR_EXECUTABLE is required and must point to a real Unity Editor binary" >&2
  exit 64
fi

if [[ -z "${GAMEUIAGENT_E2E_PACKAGE_JSON:-}" ]]; then
  echo "GAMEUIAGENT_E2E_PACKAGE_JSON is required" >&2
  exit 65
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULT_PATH="${GAMEUIAGENT_E2E_RESULT_PATH:-"$SCRIPT_DIR/Temp/gameuiagent-e2e-result.json"}"
LOG_PATH="${GAMEUIAGENT_E2E_LOG_PATH:-"$SCRIPT_DIR/Logs/gameuiagent-e2e.log"}"
mkdir -p "$(dirname "$RESULT_PATH")" "$(dirname "$LOG_PATH")"
rm -f "$RESULT_PATH"

GAMEUIAGENT_E2E_RESULT_PATH="$RESULT_PATH" "$UNITY_EDITOR_EXECUTABLE" \
  -batchmode \
  -quit \
  -nographics \
  -projectPath "$SCRIPT_DIR" \
  -executeMethod GameUIAgent.Editor.GameUIAgentE2ERunner.Run \
  -logFile "$LOG_PATH"

cat "$RESULT_PATH"
