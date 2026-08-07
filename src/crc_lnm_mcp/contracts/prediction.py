"""Single-model multimodal prediction input."""

from .common import (
    ClinicalInput,
    CtArtifactId,
    PathologyArtifactId,
    QcArtifactId,
    StrictContract,
)


class PredictMultimodalInput(StrictContract):
    qc_artifact_id: QcArtifactId
    ct_artifact_id: CtArtifactId
    pathology_artifact_id: PathologyArtifactId
    clinical: ClinicalInput


__all__ = ["PredictMultimodalInput"]