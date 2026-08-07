"""CT feature-preparation tool input."""

from typing import Literal

from .common import QcArtifactId, StrictContract


class PrecomputedCTSource(StrictContract):
    mode: Literal["precomputed"] = "precomputed"


class PrepareCTInput(StrictContract):
    qc_artifact_id: QcArtifactId
    source: PrecomputedCTSource


__all__ = ["PrepareCTInput", "PrecomputedCTSource"]