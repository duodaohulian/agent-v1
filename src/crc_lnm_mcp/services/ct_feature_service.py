"""Torch-free validation and retention of 1,409 CT features."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from .case_service import CaseAndFeatureProvider


def prepare_ct_features(
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
    schema = provider.schema()
    names = [
        *schema["ct_shape"],
        *schema["ct_original"],
        *schema["ct_wavelet"],
        *schema["ct_transformed"],
    ]
    raw = record["payloads"]["ct_features"]
    if set(raw) != set(names) or len(raw) != 1409:
        raise ValueError("CT feature keys do not match the locked schema")
    values = {name: float(raw[name]) for name in names}
    order_hash = hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()
    artifact = provider.put_artifact(
        "ct_features",
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
        "feature_count": 1409,
        "group_counts": {"shape": 14, "original": 93, "wavelet": 744, "transformed": 558},
        "ct_feature_order_sha256": order_hash,
        "compatibility": {
            "status": "validated",
            "model_compatible": True,
            "decision": "allow_prediction",
            "basis": "approved_precomputed_case_package",
            "blocking_reasons": [],
        },
    }


__all__ = ["prepare_ct_features"]
