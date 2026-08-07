from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo" / "cases" / "demo_case_001"
DESTINATION = ROOT / "src" / "crc_lnm_mcp" / "assets" / "cases" / "demo_cases.jsonl"


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    manifest = _read_object(SOURCE / "manifest.json")
    payloads = {
        "clinical": _read_object(SOURCE / "clinical.json"),
        "ct_features": _read_object(SOURCE / "ct_features.json"),
        "pathology_features": _read_object(SOURCE / "pathology_features.json"),
    }
    record = {
        "case_ref": "demo_case_001",
        "demo": True,
        "manifest": manifest,
        "payload_sha256": {
            name: hashlib.sha256(_canonical_bytes(payload)).hexdigest()
            for name, payload in payloads.items()
        },
        "payloads": payloads,
        "resource_schema_version": "1.0.12-demo",
    }
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_bytes(_canonical_bytes(record) + b"\n")
    print(DESTINATION.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
