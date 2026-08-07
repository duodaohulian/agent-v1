#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHEEL="${1:-$(find "$ROOT/dist" -maxdepth 1 -name '*.whl' -print -quit)}"
COLD_OUTPUT="${2:-$ROOT/reports/lightweight_uvx_cold_start.json}"
WARM_OUTPUT="${3:-$ROOT/reports/lightweight_uvx_warm_start.json}"
FULL_OUTPUT_DIR="${4:-$ROOT/reports/lightweight_cross_platform_gate/linux-uvx-full}"
UV="${UV:-$(command -v uv)}"
UVX="${UVX:-$(command -v uvx)}"
BASE_PYTHON="${PYTHON:-python}"
[[ -f "$WHEEL" ]] || { echo "final wheel not found" >&2; exit 1; }
"$UV" --version

AUDIT_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/crc-lnm-lightweight-uvx.XXXXXX")"
trap 'rm -rf -- "$AUDIT_ROOT"' EXIT
COLD_CACHE="$AUDIT_ROOT/cold_cache"
DEPENDENCY_CACHE="$AUDIT_ROOT/dependency-cache"
LOCK="$AUDIT_ROOT/requirements.lock"
VENV="$AUDIT_ROOT/install-venv"
DOWNLOAD_VENV="$AUDIT_ROOT/download-venv"
HARNESS_VENV="$AUDIT_ROOT/harness-venv"
mkdir -p "$COLD_CACHE" "$DEPENDENCY_CACHE"

cat >"$AUDIT_ROOT/requirements.in" <<'EOF'
fastmcp==2.14.7
pydantic==2.13.4
numpy==2.1.3
EOF

seconds() { "$BASE_PYTHON" -c 'import time; print(time.perf_counter())'; }
elapsed() { "$BASE_PYTHON" - "$1" <<'PY'
import sys, time
print(time.perf_counter() - float(sys.argv[1]))
PY
}

START="$(seconds)"
"$UV" pip compile "$AUDIT_ROOT/requirements.in" --output-file "$LOCK" --quiet
dependency_resolution_seconds="$(elapsed "$START")"

START="$(seconds)"
"$UV" venv "$DOWNLOAD_VENV" --python "$BASE_PYTHON" --quiet
UV_CACHE_DIR="$DEPENDENCY_CACHE" "$UV" pip install \
  --python "$DOWNLOAD_VENV/bin/python" --requirement "$LOCK" --quiet
dependency_download_seconds="$(elapsed "$START")"
dependency_download_bytes="$(du -sb "$DEPENDENCY_CACHE" | cut -f1)"

"$UV" venv "$VENV" --python "$BASE_PYTHON" --quiet
START="$(seconds)"
UV_CACHE_DIR="$DEPENDENCY_CACHE" "$UV" pip install --python "$VENV/bin/python" \
  --offline "$WHEEL" --quiet
dependency_install_seconds="$(elapsed "$START")"
"$UV" pip check --python "$VENV/bin/python"
installed_bytes="$(du -sb "$VENV" | cut -f1)"
site_packages_bytes="$(du -sb "$VENV"/lib/python*/site-packages | cut -f1)"

# Keep the psutil-based measurement harness outside the audited runtime environment.
"$UV" venv "$HARNESS_VENV" --python "$BASE_PYTHON" --quiet
"$UV" pip install --python "$HARNESS_VENV/bin/python" "$WHEEL" psutil --quiet

forbidden_runtime_packages="$($VENV/bin/python - <<'PY'
import importlib.util, json
names = ["torch", "torchvision", "torchaudio", "onnx", "onnxruntime"]
found = [name for name in names if importlib.util.find_spec(name) is not None]
print(json.dumps(found))
raise SystemExit(bool(found))
PY
)"

"$HARNESS_VENV/bin/python" "$ROOT/scripts/smoke_tool_05_prediction.py" --command "$UVX" \
  --server-arg=--cache-dir --server-arg="$COLD_CACHE" \
  --server-arg=--from --server-arg="$WHEEL" \
  --server-arg=crc-lnm-medical-agent \
  --output "$AUDIT_ROOT/cold.json"
cold_cache_bytes="$(du -sb "$COLD_CACHE" | cut -f1)"

"$HARNESS_VENV/bin/python" "$ROOT/scripts/smoke_tool_05_prediction.py" --command "$UVX" \
  --server-arg=--cache-dir --server-arg="$COLD_CACHE" \
  --server-arg=--from --server-arg="$WHEEL" \
  --server-arg=crc-lnm-medical-agent \
  --output "$AUDIT_ROOT/warm.json"
warm_cache_bytes="$(du -sb "$COLD_CACHE" | cut -f1)"

"$HARNESS_VENV/bin/python" "$ROOT/scripts/smoke_published_style_local_wheel.py" \
  --wheel "$WHEEL" --command "$UVX" \
  --server-arg=--cache-dir --server-arg="$COLD_CACHE" \
  --server-arg=--from --server-arg="$WHEEL" \
  --server-arg=crc-lnm-medical-agent \
  --output-dir "$FULL_OUTPUT_DIR" --output "$FULL_OUTPUT_DIR/matrix_result.json"

"$VENV/bin/python" - "$AUDIT_ROOT/cold.json" "$AUDIT_ROOT/warm.json" \
  "$COLD_OUTPUT" "$WARM_OUTPUT" "$dependency_resolution_seconds" \
  "$dependency_download_seconds" "$dependency_install_seconds" \
  "$dependency_download_bytes" "$installed_bytes" "$site_packages_bytes" \
  "$cold_cache_bytes" "$warm_cache_bytes" "$WHEEL" "$UV" \
  "$forbidden_runtime_packages" <<'PY'
import json, os, platform, subprocess, sys
from pathlib import Path

cold = json.loads(Path(sys.argv[1]).read_text())
warm = json.loads(Path(sys.argv[2]).read_text())
common = {
    "status": "PASS",
    "platform": platform.platform(),
    "python_version": platform.python_version(),
    "uv_version": subprocess.check_output([sys.argv[14], "--version"], text=True).strip(),
    "dependency_resolution_seconds": float(sys.argv[5]),
    "dependency_download_seconds": float(sys.argv[6]),
    "dependency_install_seconds": float(sys.argv[7]),
    "dependency_download_bytes": int(sys.argv[8]),
    "installed_bytes": int(sys.argv[9]),
    "site_packages_bytes": int(sys.argv[10]),
    "wheel_size_bytes": os.path.getsize(sys.argv[13]),
    "forbidden_runtime_packages": json.loads(sys.argv[15]),
}
cold_report = {
    **common,
    "cache_state": "cold",
    "uv_cache_bytes": int(sys.argv[11]),
    "smoke": cold,
    "initialize_seconds": cold["timings"]["initialize_seconds"],
    "tools_list_seconds": cold["timings"]["tools_list_seconds"],
    "first_prediction_seconds": cold["timings"]["crc_lnm_predict_multimodal_seconds_1"],
    "second_prediction_seconds": cold["timings"]["crc_lnm_predict_multimodal_seconds_2"],
    "peak_rss_bytes": cold["peak_rss_bytes"],
}
warm_report = {
    **common,
    "cache_state": "warm",
    "uv_cache_bytes": int(sys.argv[12]),
    "smoke": warm,
    "initialize_seconds": warm["timings"]["initialize_seconds"],
    "tools_list_seconds": warm["timings"]["tools_list_seconds"],
    "first_prediction_seconds": warm["timings"]["crc_lnm_predict_multimodal_seconds_1"],
    "second_prediction_seconds": warm["timings"]["crc_lnm_predict_multimodal_seconds_2"],
    "peak_rss_bytes": warm["peak_rss_bytes"],
}
for output, report in ((Path(sys.argv[3]), cold_report), (Path(sys.argv[4]), warm_report)):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
PY
