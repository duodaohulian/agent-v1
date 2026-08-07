from __future__ import annotations

from enum import Enum
from pathlib import Path

from crc_lnm_mcp.errors import ErrorCode

ROOT = Path(__file__).resolve().parents[1]


def test_error_codes_use_python_310_compatible_string_enum() -> None:
    source = (ROOT / "src/crc_lnm_mcp/errors.py").read_text("utf-8")
    assert "StrEnum" not in source
    assert issubclass(ErrorCode, str)
    assert issubclass(ErrorCode, Enum)
    assert str(ErrorCode.SERVICE_UNAVAILABLE) == ErrorCode.SERVICE_UNAVAILABLE.value


def test_packaged_source_does_not_import_datetime_utc() -> None:
    packaged_source = ROOT / "src/crc_lnm_mcp"
    offenders = [
        path.relative_to(packaged_source).as_posix()
        for path in packaged_source.rglob("*.py")
        if "from datetime import UTC" in path.read_text("utf-8")
    ]
    assert offenders == []


def test_traversable_uses_python_310_import_location() -> None:
    source = (ROOT / "src/crc_lnm_mcp/settings.py").read_text("utf-8")
    assert "from importlib.abc import Traversable" in source
    assert "from importlib.resources.abc import Traversable" not in source
