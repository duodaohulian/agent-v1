from __future__ import annotations

import json
from importlib.resources import as_file
from pathlib import Path
from uuid import uuid4

import numpy as np

from crc_lnm_mcp.inference.preprocessing import NumpyPreprocessor
from crc_lnm_mcp.runtime import RuntimeProvider
from crc_lnm_mcp.settings import package_asset

ROOT = Path(__file__).resolve().parents[1]


def _demo_arrays() -> object:
    runtime = RuntimeProvider()
    trace_id = uuid4()
    qc = runtime.cases.case_data_qc("demo_case_001", request_id=uuid4(), trace_id=trace_id)
    ct_ref = runtime.cases.prepare_ct_features(
        "demo_case_001",
        qc_artifact_id=qc["artifact"]["artifact_id"],
        request_id=uuid4(),
        trace_id=trace_id,
    )
    pathology_ref = runtime.cases.prepare_pathology_features(
        "demo_case_001",
        qc_artifact_id=qc["artifact"]["artifact_id"],
        request_id=uuid4(),
        trace_id=trace_id,
    )
    ct = runtime.cases.require_artifact(
        ct_ref["artifact"]["artifact_id"],
        trace_id=trace_id,
        case_ref="demo_case_001",
        expected_type="ct_features",
    ).payload["values"]
    pathology = runtime.cases.require_artifact(
        pathology_ref["artifact"]["artifact_id"],
        trace_id=trace_id,
        case_ref="demo_case_001",
        expected_type="pathology_features",
    ).payload["values"]
    schema = json.loads(package_asset("schemas", "schema.json").read_text("utf-8"))
    with (
        as_file(package_asset("preprocessors", "preprocessing.json")) as metadata,
        as_file(package_asset("preprocessors", "preprocessing.npz")) as values,
    ):
        preprocessor = NumpyPreprocessor.from_files(schema, metadata, values)
    return preprocessor.transform(
        pathology,
        ct,
        {"age": 60, "male": 0, "Type": 1, "T": 1},
    )


def test_numpy_model_matches_torch_logits_and_exposes_layer_trace(
    torch_model_state: Path,
) -> None:
    import torch

    from crc_lnm_mcp.inference.numpy_model import NumpyMCAT
    from scripts.torch_reference_model import MultimodalBatch, build_model, remap_state_dict

    prepared = _demo_arrays()
    runtime_path = ROOT / "src/crc_lnm_mcp/assets/model/model_runtime.npz"
    with np.load(runtime_path, allow_pickle=False) as archive:
        parameters = {name: archive[name].copy() for name in archive.files}
    numpy_model = NumpyMCAT(parameters)
    actual, trace = numpy_model.forward(prepared, collect_trace=True)

    config = json.loads(
        (ROOT / "src/crc_lnm_mcp/assets/model/model_config.json").read_text("utf-8")
    )
    torch_model = build_model(config)
    state = torch.load(torch_model_state, weights_only=True, map_location="cpu")
    torch_model.load_state_dict(remap_state_dict(state), strict=True)
    torch_model.eval()
    batch = MultimodalBatch(
        **{
            name: torch.from_numpy(getattr(prepared, name))
            for name in (
                "pathology",
                "ct_shape",
                "ct_original",
                "ct_wavelet",
                "ct_transformed",
                "age",
                "male",
                "type_index",
                "t_stage_index",
            )
        }
    )
    with torch.inference_mode():
        expected = torch_model(batch).numpy()
    np.testing.assert_allclose(actual, expected, atol=1e-5, rtol=1e-5)
    assert actual.dtype == np.float32
    for required in (
        "path_encoder.linear_1",
        "path_encoder.layer_norm_2",
        "clinical_encoder.output",
        "cross_attention.output",
        "classifier.logits",
    ):
        assert required in trace
