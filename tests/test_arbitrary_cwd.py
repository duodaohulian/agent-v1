from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def test_installed_console_script_runs_from_arbitrary_cwd(tmp_path: Path) -> None:
    command = os.environ.get("CANARY_CONSOLE")
    if not command:
        pytest.skip("CANARY_CONSOLE is set in the wheel-only environment")
    smoke = Path(__file__).resolve().parents[1] / "scripts/smoke_stdio.py"
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    result = subprocess.run(
        [os.fspath(Path(os.sys.executable)), os.fspath(smoke), "--command", command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    assert before == after
