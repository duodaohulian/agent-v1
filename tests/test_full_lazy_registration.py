from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from crc_lnm_mcp import server

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = {
    "crc_lnm_get_model_info",
    "crc_lnm_case_data_qc",
    "crc_lnm_prepare_ct_features",
    "crc_lnm_prepare_pathology_features",
    "crc_lnm_predict_multimodal",
    "crc_lnm_generate_report",
}


def test_exact_six_tools() -> None:
    assert set(asyncio.run(server.mcp.get_tools())) == EXPECTED_TOOLS


def test_six_tools_are_independent_modules() -> None:
    expected_modules = {
        "get_model_info",
        "case_data_qc",
        "prepare_ct_features",
        "prepare_pathology_features",
        "predict_multimodal",
        "generate_report",
    }
    tools_directory = ROOT / "src" / "crc_lnm_mcp" / "tools"
    assert {path.stem for path in tools_directory.glob("*.py")} >= expected_modules


def test_list_tools_succeeds_when_torch_import_is_blocked() -> None:
    code = """
import asyncio
import builtins
import sys

original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == 'torch' or name.startswith('torch.'):
        raise RuntimeError('torch import blocked during registration')
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import

from crc_lnm_mcp import server
names = set(asyncio.run(server.mcp.get_tools()))
assert names == {
    'crc_lnm_get_model_info',
    'crc_lnm_case_data_qc',
    'crc_lnm_prepare_ct_features',
    'crc_lnm_prepare_pathology_features',
    'crc_lnm_predict_multimodal',
    'crc_lnm_generate_report',
}
assert not any(name == 'torch' or name.startswith('torch.') for name in sys.modules)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_server_module_has_no_heavy_top_level_imports() -> None:
    source = (ROOT / "src" / "crc_lnm_mcp" / "server.py").read_text(encoding="utf-8")
    forbidden = ("import torch", "import pandas", "import sklearn", "PredictionService(")
    assert all(token not in source for token in forbidden)
