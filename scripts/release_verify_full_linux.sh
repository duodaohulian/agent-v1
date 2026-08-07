#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHEEL="$(find "$ROOT/dist" -maxdepth 1 -name '*.whl' -print -quit)"
[[ -f "$WHEEL" ]] || { echo "final wheel not found" >&2; exit 1; }

GATE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/crc-lnm-linux-gate.XXXXXX")"
trap 'rm -rf -- "$GATE_ROOT"' EXIT
BASE_PYTHON="${PYTHON:-python}"
UV="${UV:-$(command -v uv || true)}"
if [[ -n "$UV" ]]; then
  "$UV" venv --python "$BASE_PYTHON" "$GATE_ROOT/venv"
else
  "$BASE_PYTHON" -m venv "$GATE_ROOT/venv"
fi
PYTHON="$GATE_ROOT/venv/bin/python"
CONSOLE="$GATE_ROOT/venv/bin/crc-lnm-medical-agent"
if [[ -n "$UV" ]]; then
  "$UV" pip install --python "$PYTHON" "$WHEEL" pytest psutil
  "$UV" pip check --python "$PYTHON"
else
  "$PYTHON" -m pip install "$WHEEL" pytest psutil
  "$PYTHON" -m pip check
fi
"$PYTHON" -c "import importlib.util; assert importlib.util.find_spec('torch') is None"

(cd "$GATE_ROOT" && "$PYTHON" -I -B -c \
  'import crc_lnm_mcp; assert "site-packages" in crc_lnm_mcp.__file__; print(crc_lnm_mcp.__file__)')

REPORT_BASE="${REPORT_BASE:-$ROOT/reports/lightweight_cross_platform_gate}"
REPORT_ROOT="$REPORT_BASE/linux-$("$PYTHON" -c 'import sys; print(f"py{sys.version_info.major}{sys.version_info.minor}")')"
mkdir -p "$REPORT_ROOT"
SMOKE_SCRIPTS=(
  smoke_tool_01_model_info.py
  smoke_tool_02_case_qc.py
  smoke_tool_03_ct_features.py
  smoke_tool_04_pathology_features.py
  smoke_tool_05_prediction.py
  smoke_tool_06_report.py
  smoke_all_six_tools.py
)
for smoke in "${SMOKE_SCRIPTS[@]}"; do
  "$PYTHON" "$ROOT/scripts/$smoke" --command "$CONSOLE" \
    --output "$REPORT_ROOT/${smoke%.py}.json"
done
"$PYTHON" "$ROOT/scripts/smoke_published_style_local_wheel.py" \
  --wheel "$WHEEL" --command "$CONSOLE" --invariants-only \
  --output "$REPORT_ROOT/matrix_result.json"

echo "LINUX FULL RELEASE VERIFICATION: PASS"
