"""Artifact-only report generation input."""

from .common import PredictionArtifactId, QcArtifactId, StrictContract


class GenerateReportInput(StrictContract):
    qc_artifact_id: QcArtifactId
    prediction_artifact_id: PredictionArtifactId


__all__ = ["GenerateReportInput"]