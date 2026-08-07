"""Deterministic escaped report generation from existing artifacts only."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from .case_service import CaseAndFeatureProvider

SECTIONS = [
    "case_summary",
    "input_quality",
    "model_score",
    "limitations",
    "expert_review",
    "safety_statement",
]
SAFETY_STATEMENT = (
    "For research assistance only; this output is not a diagnosis and requires expert review."
)


def generate_report(
    provider: CaseAndFeatureProvider,
    case_ref: str,
    *,
    qc_artifact_id: str,
    prediction_artifact_id: str,
    request_id: UUID,
    trace_id: UUID,
) -> dict[str, Any]:
    del request_id
    _record, binding = provider.validated_case(case_ref)
    qc = provider.require_artifact(
        qc_artifact_id,
        trace_id=trace_id,
        case_ref=case_ref,
        expected_type="case_qc",
    )
    prediction = provider.require_artifact(
        prediction_artifact_id,
        trace_id=trace_id,
        case_ref=case_ref,
        expected_type="prediction",
    )
    if qc.case_binding_sha256 != binding or prediction.case_binding_sha256 != binding:
        raise ValueError("report artifacts do not match the case binding")
    value = prediction.payload
    html = (
        '<!doctype html><html><head><meta charset="utf-8">'
        "<title>CRC-LNM Research Report</title></head><body>"
        f'<section id="case_summary"><h2>Case summary</h2><p>{escape(case_ref)}</p>'
        "</section>"
        '<section id="input_quality"><h2>Input quality</h2>'
        "<p>QC passed for the packaged synthetic demo case.</p></section>"
        '<section id="model_score"><h2>Model score</h2>'
        f"<p>Probability: {float(value['positive_probability']):.6f}; "
        f"threshold: {float(value['threshold']):.6f}; "
        f"class: {int(value['predicted_class'])}.</p>"
        f"<p>Selected single-model: {escape(str(value['selected_model_id']))}; "
        "member count: 1.</p></section>"
        '<section id="limitations"><h2>Limitations</h2>'
        "<p>The former ensemble threshold has not been recalibrated for this "
        "single-model deployment. No independent-test claim is made.</p></section>"
        '<section id="expert_review"><h2>Expert review</h2>'
        "<p>Qualified clinical review is required.</p></section>"
        '<section id="safety_statement"><h2>Safety statement</h2>'
        f"<p>{escape(SAFETY_STATEMENT)}</p></section>"
        "</body></html>"
    )
    artifact = provider.put_artifact(
        "report",
        trace_id=trace_id,
        case_ref=case_ref,
        case_binding_sha256=binding,
        payload=html,
    )
    return {
        "artifact": artifact.public_ref(),
        "report_format": "html",
        "report_resource_available": False,
        "sections": SECTIONS,
        "heatmap_status": "not_available_in_v1",
        "feature_attribution_status": "not_available_in_v1",
        "ct_source_used": "precomputed",
        "fallback_disclosed": False,
        "safety_statement": SAFETY_STATEMENT,
    }


__all__ = ["generate_report"]
