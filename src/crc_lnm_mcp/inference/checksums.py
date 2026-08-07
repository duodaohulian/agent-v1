"""Shared checksum helpers for structured inference assets."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from crc_lnm_mcp.settings import MAX_METADATA_BYTES


def canonical_json_bytes(resource: Any) -> bytes:
    """Return a stable UTF-8 representation of a size-bounded JSON resource."""
    with resource.open("rb") as handle:
        raw = handle.read(MAX_METADATA_BYTES + 1)
    if len(raw) > MAX_METADATA_BYTES:
        raise RuntimeError("model JSON exceeds size limit")
    value = json.loads(raw.decode("utf-8"))
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(resource: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(resource)).hexdigest()


__all__ = ["canonical_json_bytes", "canonical_json_sha256"]
