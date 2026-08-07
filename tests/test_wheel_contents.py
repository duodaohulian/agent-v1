from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest


def _wheel() -> Path:
    configured = os.environ.get("CANARY_WHEEL")
    if not configured:
        pytest.skip("CANARY_WHEEL is set during clean artifact verification")
    return Path(configured).resolve()


def test_wheel_contains_full_runtime_and_exactly_one_numpy_model() -> None:
    with zipfile.ZipFile(_wheel()) as archive:
        names = archive.namelist()
    assert names
    assert all(name.startswith("crc_lnm_mcp/") or ".dist-info/" in name for name in names)
    assert not any(
        token in name.lower()
        for name in names
        for token in (
            "wei_multimodal",
            "deployment_bundle",
            ".pt",
            ".pth",
            ".ckpt",
            "__pycache__",
            ".pyc",
        )
    )
    runtime_models = [
        name
        for name in names
        if "/assets/model/" in name and name.lower().endswith((".npz", ".onnx"))
    ]
    assert runtime_models == ["crc_lnm_mcp/assets/model/model_runtime.npz"]
    assert "crc_lnm_mcp/assets/cases/demo_cases.jsonl" in names
    assert "crc_lnm_mcp/assets/model/deployment_manifest.json" in names
