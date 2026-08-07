from __future__ import annotations

import builtins
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from crc_lnm_mcp.runtime import RuntimeProvider

ROOT = Path(__file__).resolve().parents[1]


def _schema() -> dict[str, object]:
    path = ROOT / "src" / "crc_lnm_mcp" / "assets" / "schemas" / "schema.json"
    assert path.is_file()
    return json.loads(path.read_text(encoding="utf-8"))


def _order_hash(names: list[str]) -> str:
    return hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()


def test_ct_features_preserve_locked_dimension_and_order_without_torch(monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "torch" or name.startswith("torch."):
            raise RuntimeError("torch import blocked for CT operation")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    runtime = RuntimeProvider()
    trace_id = uuid4()
    qc = runtime.cases.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=trace_id)
    result = runtime.cases.prepare_ct_features(
        "demo_case_001",
        qc_artifact_id=qc["artifact"]["artifact_id"],
        request_id=uuid4(),
        trace_id=trace_id,
    )
    schema = _schema()
    expected_names = [
        *schema["ct_shape"],
        *schema["ct_original"],
        *schema["ct_wavelet"],
        *schema["ct_transformed"],
    ]
    assert result["feature_count"] == 1409
    assert result["group_counts"] == {
        "shape": 14,
        "original": 93,
        "wavelet": 744,
        "transformed": 558,
    }
    assert result["ct_feature_order_sha256"] == _order_hash(expected_names)
    artifact = runtime.cases.require_artifact(
        result["artifact"]["artifact_id"],
        trace_id=trace_id,
        case_ref="demo_case_001",
        expected_type="ct_features",
    )
    assert list(artifact.payload["values"]) == expected_names


def test_pathology_features_preserve_locked_dimension_and_order_without_torch() -> None:
    runtime = RuntimeProvider()
    trace_id = uuid4()
    qc = runtime.cases.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=trace_id)
    result = runtime.cases.prepare_pathology_features(
        "demo_case_001",
        qc_artifact_id=qc["artifact"]["artifact_id"],
        request_id=uuid4(),
        trace_id=trace_id,
    )
    expected_names = _schema()["pathology_features"]
    assert result["feature_count"] == 768
    assert result["pathology_feature_order_sha256"] == _order_hash(expected_names)
    artifact = runtime.cases.require_artifact(
        result["artifact"]["artifact_id"],
        trace_id=trace_id,
        case_ref="demo_case_001",
        expected_type="pathology_features",
    )
    assert list(artifact.payload["values"]) == expected_names


def test_feature_preparation_requires_same_trace_qc_artifact() -> None:
    runtime = RuntimeProvider()
    trace_id = uuid4()
    qc = runtime.cases.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=trace_id)
    with pytest.raises(ValueError, match="trace"):
        runtime.cases.prepare_ct_features(
            "demo_case_001",
            qc_artifact_id=qc["artifact"]["artifact_id"],
            request_id=uuid4(),
            trace_id=uuid4(),
        )
