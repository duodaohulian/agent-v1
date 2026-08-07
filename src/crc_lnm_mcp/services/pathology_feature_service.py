"""Torch-free validation and retention of 768 pathology features."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from .case_service import CaseAndFeatureProvider


def prepare_pathology_features(
    provider: CaseAndFeatureProvider,
    case_ref: str,
    *,
    qc_artifact_id: str,
    request_id: UUID,
    trace_id: UUID,
) -> dict[str, Any]:
    del request_id
    record, binding = provider.validated_case(case_ref)
    qc = provider.require_artifact(
        qc_artifact_id,
        trace_id=trace_id,
        case_ref=case_ref,
        expected_type="case_qc",
    )
    if qc.case_binding_sha256 != binding or qc.payload.get("passed") is not True:
        raise ValueError("QC artifact is not valid for this case")
    names = list(provider.schema()["pathology_features"])
    raw = record["payloads"]["pathology_features"]
    if set(raw) != set(names) or len(raw) != 768:
        raise ValueError("pathology feature keys do not match the locked schema")
    values = {name: float(raw[name]) for name in names}
    order_hash = hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()
    artifact = provider.put_artifact(
        "pathology_features",
        trace_id=trace_id,
        case_ref=case_ref,
        case_binding_sha256=binding,
        payload={
            "values": values,
            "feature_order_sha256": order_hash,
            "source_type": "precomputed_features",
        },
    )
    return {
        "artifact": artifact.public_ref(),
        "input_mode": "precomputed",
        "extraction_performed": False,
        "source_type": "precomputed_features",
        "feature_count": 768,
        "pathology_feature_order_sha256": order_hash,
        "heatmap_status": "not_available_in_v1",
    }


__all__ = ["prepare_pathology_features"]
