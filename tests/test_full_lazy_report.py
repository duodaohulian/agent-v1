from __future__ import annotations

from uuid import uuid4

import pytest

from crc_lnm_mcp.runtime import RuntimeProvider


def _artifacts(runtime: RuntimeProvider):
    trace_id = uuid4()
    qc = runtime.cases.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=trace_id)
    _record, binding = runtime.cases.validated_case("demo_case_001")
    prediction = runtime.cases.put_artifact(
        "prediction",
        trace_id=trace_id,
        case_ref="demo_case_001",
        case_binding_sha256=binding,
        payload={
            "positive_probability": 0.5726384520530701,
            "threshold": 0.3529504342004657,
            "predicted_class": 1,
            "selected_model_id": "seed_2024",
            "selected_seed": 2024,
            "member_count": 1,
            "ensemble_enabled": False,
        },
    )
    return trace_id, qc["artifact"]["artifact_id"], prediction.artifact_id


def test_report_from_existing_artifact_does_not_load_model() -> None:
    runtime = RuntimeProvider()
    trace_id, qc_id, prediction_id = _artifacts(runtime)
    assert runtime.prediction.load_count == 0
    result = runtime.cases.generate_report(
        "demo_case_001",
        qc_artifact_id=qc_id,
        prediction_artifact_id=prediction_id,
        request_id=uuid4(),
        trace_id=trace_id,
    )
    assert runtime.prediction.load_count == 0
    assert result["report_format"] == "html"
    assert result["sections"] == [
        "case_summary",
        "input_quality",
        "model_score",
        "limitations",
        "expert_review",
        "safety_statement",
    ]
    assert result["safety_statement"]
    artifact = runtime.cases.require_artifact(
        result["artifact"]["artifact_id"],
        trace_id=trace_id,
        case_ref="demo_case_001",
        expected_type="report",
    )
    assert "0.572638" in artifact.payload
    assert "single-model" in artifact.payload
    assert "research" in artifact.payload.lower()


def test_report_rejects_cross_trace_prediction_artifact() -> None:
    runtime = RuntimeProvider()
    trace_id, qc_id, prediction_id = _artifacts(runtime)
    with pytest.raises(ValueError, match="trace"):
        runtime.cases.generate_report(
            "demo_case_001",
            qc_artifact_id=qc_id,
            prediction_artifact_id=prediction_id,
            request_id=uuid4(),
            trace_id=uuid4(),
        )
