"""Pathology feature-preparation tool input."""

from .common import QcArtifactId, StrictContract


class PreparePathologyInput(StrictContract):
    qc_artifact_id: QcArtifactId


__all__ = ["PreparePathologyInput"]