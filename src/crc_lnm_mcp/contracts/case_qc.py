"""Case quality-control tool input."""

from typing import Literal

from .common import StrictContract


class CaseQCInput(StrictContract):
    ct_source_preference: Literal["precomputed"] = "precomputed"
    fallback_policy: Literal["precomputed_if_available"] = "precomputed_if_available"


__all__ = ["CaseQCInput"]