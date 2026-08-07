"""Bounded package-resource settings for the full lazy runtime."""

from importlib.abc import Traversable
from importlib.resources import files

MAX_METADATA_BYTES = 128 * 1024
MAX_CASE_RESOURCE_BYTES = 32 * 1024 * 1024
MAX_CASE_RECORD_BYTES = 2 * 1024 * 1024


def package_asset(*parts: str) -> Traversable:
    """Resolve a fixed package-owned asset without accepting user path input."""

    resource = files("crc_lnm_mcp").joinpath("assets")
    for part in parts:
        if not part or part in {".", ".."} or "/" in part or "\\" in part:
            raise ValueError("asset component is unsafe")
        resource = resource.joinpath(part)
    return resource


__all__ = [
    "MAX_CASE_RECORD_BYTES",
    "MAX_CASE_RESOURCE_BYTES",
    "MAX_METADATA_BYTES",
    "package_asset",
]
