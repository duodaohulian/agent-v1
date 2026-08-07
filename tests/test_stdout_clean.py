from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_canary_source_has_no_print_or_stdout_logging_configuration() -> None:
    for path in (ROOT / "src/crc_lnm_mcp").glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", f"stdout print in {path}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert not (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "logging"
                    and node.func.attr == "basicConfig"
                ), f"logging.basicConfig in {path}"
