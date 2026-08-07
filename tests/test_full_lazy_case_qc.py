from __future__ import annotations

import builtins
import json
from pathlib import Path
from uuid import uuid4

import pytest

from crc_lnm_mcp.runtime import RuntimeProvider

ROOT = Path(__file__).resolve().parents[1]


def test_case_qc_builds_index_only_on_first_case_call(monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "torch" or name.startswith("torch."):
            raise RuntimeError("torch import blocked for case operation")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    provider = RuntimeProvider().cases
    assert provider.indexed_record_count == 0
    result = provider.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=uuid4())
    assert result["passed"] is True
    assert result["case_ref"] == "demo_case_001"
    assert result["demo"] is True
    assert result["modalities"] == {
        "ct": "present",
        "pathology": "present",
        "clinical": "present",
    }
    assert result["privacy_check"] == "passed"
    assert result["artifact"]["artifact_id"].startswith("qc_")
    assert provider.indexed_record_count == 1


@pytest.mark.parametrize(
    "case_ref",
    ["../manifest", "C:\\secret", "/tmp/case", "demo/case", "..", ""],
)
def test_case_ref_allowlist_rejects_paths(case_ref: str) -> None:
    provider = RuntimeProvider().cases
    with pytest.raises(ValueError, match="case_ref"):
        provider.case_data_qc(case_ref, request_id=uuid4(), trace_id=uuid4())
    assert provider.indexed_record_count == 0


def test_unknown_allowlisted_case_is_not_resolved_as_a_path() -> None:
    provider = RuntimeProvider().cases
    with pytest.raises(KeyError, match="case_ref is not available"):
        provider.case_data_qc("unknown_case", request_id=uuid4(), trace_id=uuid4())


def test_packaged_case_resource_contains_only_one_marked_demo() -> None:
    resource = ROOT / "src" / "crc_lnm_mcp" / "assets" / "cases" / "demo_cases.jsonl"
    assert resource.is_file()
    lines = resource.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["case_ref"] == "demo_case_001"
    assert record["demo"] is True
    assert "18-01219" not in lines[0]


def test_qc_artifact_is_trace_and_case_bound() -> None:
    provider = RuntimeProvider().cases
    trace_id = uuid4()
    result = provider.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=trace_id)
    artifact_id = result["artifact"]["artifact_id"]
    artifact = provider.require_artifact(
        artifact_id,
        trace_id=trace_id,
        case_ref="demo_case_001",
        expected_type="case_qc",
    )
    assert artifact.payload["passed"] is True
    with pytest.raises(ValueError, match="trace"):
        provider.require_artifact(
            artifact_id,
            trace_id=uuid4(),
            case_ref="demo_case_001",
            expected_type="case_qc",
        )
