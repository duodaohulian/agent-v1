from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {
    "torch",
    "pandas",
    "numpy",
    "sklearn",
    "imblearn",
    "uvicorn",
    "starlette",
    "wei_multimodal",
}


def test_canary_import_does_not_load_medical_or_http_stack(tmp_path: Path) -> None:
    code = """
import json
import sys
import crc_lnm_mcp.server
print(json.dumps(sorted(sys.modules)))
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    # Isolated mode ignores PYTHONPATH, so add the source path explicitly while
    # preserving isolation from user site packages and the repository CWD.
    if result.returncode != 0 and os.environ.get("CANARY_INSTALLED") != "1":
        code = f"import sys; sys.path.insert(0, {str(ROOT / 'src')!r});" + code
        result = subprocess.run(
            [sys.executable, "-I", "-c", code],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    assert result.returncode == 0, result.stderr
    loaded = set(json.loads(result.stdout))
    assert FORBIDDEN.isdisjoint(loaded)


def test_canary_module_import_has_no_filesystem_side_effects(tmp_path: Path) -> None:
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    source_prefix = (
        ""
        if os.environ.get("CANARY_INSTALLED") == "1"
        else f"import sys; sys.path.insert(0, {str(ROOT / 'src')!r}); "
    )
    code = source_prefix + "import crc_lnm_mcp"
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert before == after
