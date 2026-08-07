"""Resolve protected Torch reference assets only from explicit configuration."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from pathlib import Path

MODEL_STATE_ENV = "CRC_LNM_TORCH_MODEL_STATE"
REFERENCE_ROOT_ENV = "CRC_LNM_TORCH_REFERENCE_ROOT"
MODEL_STATE_RELATIVE_PATH = Path("src/crc_lnm_mcp/assets/model/model_state.pt")
SOURCE_SHA256 = "40e9fbed0da4fa915626e5c0bc6874a10a9129448271614fd011d31c46deeb17"


def resolve_model_state(environment: Mapping[str, str] | None = None) -> Path | None:
    """Return an explicitly configured model state, never a guessed repository path."""

    values = os.environ if environment is None else environment
    direct = values.get(MODEL_STATE_ENV)
    if direct:
        candidate = Path(direct).expanduser().resolve()
        return candidate if candidate.is_file() else None
    root = values.get(REFERENCE_ROOT_ENV)
    if root:
        candidate = Path(root).expanduser().resolve() / MODEL_STATE_RELATIVE_PATH
        return candidate if candidate.is_file() else None
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_model_state(path: Path) -> Path:
    """Validate the protected seed_2024 state without copying it into the project."""

    if sha256_file(path) != SOURCE_SHA256:
        raise RuntimeError("Torch reference asset checksum mismatch")
    return path
