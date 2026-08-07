from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "smoke_tool_01_model_info.py",
    "smoke_tool_02_case_qc.py",
    "smoke_tool_03_ct_features.py",
    "smoke_tool_04_pathology_features.py",
    "smoke_tool_05_prediction.py",
    "smoke_tool_06_report.py",
    "smoke_all_six_tools.py",
]


def _run(name: str, timeout: int = 45) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    value = json.loads(completed.stdout)
    assert isinstance(value, dict)
    return value


def test_each_tool_has_an_independent_smoke_script() -> None:
    for name in SCRIPTS:
        assert (ROOT / "scripts" / name).is_file(), name


def test_model_info_independent_stdio_smoke() -> None:
    report = _run("smoke_tool_01_model_info.py")
    assert report["status"] == "PASS"
    assert report["target_tool"] == "crc_lnm_get_model_info"
    assert len(report["tools"]) == 6
    assert report["leaked_child_processes"] == []
    assert report["network_violations"] == []
    assert report["cwd_files_created"] == []


def test_full_six_tool_stdio_pipeline() -> None:
    report = _run("smoke_all_six_tools.py", timeout=90)
    assert report["status"] == "PASS"
    assert report["called_tools"] == [
        "crc_lnm_get_model_info",
        "crc_lnm_case_data_qc",
        "crc_lnm_prepare_ct_features",
        "crc_lnm_prepare_pathology_features",
        "crc_lnm_predict_multimodal",
        "crc_lnm_generate_report",
    ]
    assert report["prediction"]["member_count"] == 1
    assert report["prediction"]["ensemble_enabled"] is False
    assert report["prediction"]["selected_model_id"] == "seed_2024"
    assert report["leaked_child_processes"] == []
    assert report["network_violations"] == []
    assert report["cwd_files_created"] == []
