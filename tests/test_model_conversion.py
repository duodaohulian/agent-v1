from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def test_converter_writes_safe_complete_deterministic_assets(
    tmp_path: Path, torch_model_state: Path
) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts/convert_torch_to_numpy.py"),
        "--source",
        str(torch_model_state),
        "--output-dir",
        str(tmp_path),
    ]
    first = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    assert first.returncode == 0, first.stderr.decode(errors="replace")
    runtime = tmp_path / "model_runtime.npz"
    manifest_path = tmp_path / "conversion_manifest.json"
    assert runtime.is_file()
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text("utf-8"))
    assert manifest["parameter_count"] == 763842
    assert len(manifest["arrays"]) == 66
    with np.load(runtime, allow_pickle=False) as arrays:
        assert sorted(arrays.files) == sorted(row["asset_key"] for row in manifest["arrays"])
        assert sum(arrays[name].size for name in arrays.files) == 763842
        assert all(arrays[name].dtype == np.float32 for name in arrays.files)
        assert all(np.isfinite(arrays[name]).all() for name in arrays.files)
    original_hash = manifest["runtime_asset_sha256"]
    second = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    assert second.returncode == 0, second.stderr.decode(errors="replace")
    assert json.loads(manifest_path.read_text("utf-8"))["runtime_asset_sha256"] == original_hash
