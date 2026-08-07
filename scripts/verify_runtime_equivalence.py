"""Generate Torch-to-NumPy aggregate and layerwise equivalence evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch_reference_model import MultimodalBatch, build_model, remap_state_dict
from torch_reference_paths import resolve_model_state, validate_model_state

from crc_lnm_mcp.inference.numpy_model import NumpyMCAT
from crc_lnm_mcp.inference.numpy_ops import softmax
from crc_lnm_mcp.inference.preprocessing import NumpyPreprocessor, PreparedArrays

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DEMO = 0.5726384520530701
THRESHOLD = 0.3529504342004657


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def load_demo() -> tuple[dict[str, float], dict[str, float], dict[str, int | float]]:
    path = ROOT / "src/crc_lnm_mcp/assets/cases/demo_cases.jsonl"
    line = path.read_text("utf-8").splitlines()[0]
    payloads = json.loads(line)["payloads"]
    return payloads["pathology_features"], payloads["ct_features"], payloads["clinical"]


def prepared_to_torch(prepared: PreparedArrays) -> MultimodalBatch:
    return MultimodalBatch(
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


def synthetic_cases(
    preprocessor: NumpyPreprocessor, count: int = 100
) -> list[tuple[dict[str, float], dict[str, float], dict[str, int | float]]]:
    rng = np.random.default_rng(20240805)
    cases = []
    types = [1, 2, 3]
    stages: list[int | float] = [1, 2, 3, 3.2, 4, 4.1, 4.2]
    for index in range(count):
        pathology: dict[str, float] = {}
        ct: dict[str, float] = {}
        age = 60.0
        for group, columns in preprocessor.group_columns.items():
            if index == 0:
                standardized = np.zeros(len(columns), dtype=np.float64)
            elif index == 1:
                standardized = np.full(len(columns), -1.0, dtype=np.float64)
            elif index == 2:
                standardized = np.linspace(-3.0, 3.0, len(columns), dtype=np.float64)
            else:
                standardized = np.clip(rng.normal(size=len(columns)), -3.0, 3.0)
            raw = preprocessor.means[group] + preprocessor.scales[group] * standardized
            for column, value in zip(columns, raw, strict=True):
                if column.startswith("pathology::"):
                    pathology[column.removeprefix("pathology::")] = float(value)
                elif column.startswith("ct::"):
                    ct[column.removeprefix("ct::")] = float(value)
                elif column == "age":
                    age = float(value)
        cases.append(
            (
                pathology,
                ct,
                {
                    "age": age,
                    "male": index % 2,
                    "Type": types[index % len(types)],
                    "T": stages[index % len(stages)],
                },
            )
        )
    return cases


def reference_trace(model: torch.nn.Module, batch: MultimodalBatch) -> dict[str, np.ndarray]:
    mapping = {
        "path_encoder.network.0": "path_encoder.linear_1",
        "path_encoder.network.1": "path_encoder.gelu_1",
        "path_encoder.network.2": "path_encoder.layer_norm_1",
        "path_encoder.network.4": "path_encoder.linear_2",
        "path_encoder.network.5": "path_encoder.gelu_2",
        "path_encoder.network.6": "path_encoder.layer_norm_2",
        "clinical_encoder.continuous_encoder.0": "clinical_encoder.continuous_linear",
        "clinical_encoder.continuous_encoder.1": "clinical_encoder.continuous_gelu",
        "clinical_encoder.continuous_encoder.2": "clinical_encoder.continuous_layer_norm",
        "clinical_encoder.projection.0": "clinical_encoder.projection_linear_1",
        "clinical_encoder.projection.1": "clinical_encoder.projection_gelu_1",
        "clinical_encoder.projection.2": "clinical_encoder.projection_layer_norm_1",
        "clinical_encoder.projection.4": "clinical_encoder.projection_linear_2",
        "clinical_encoder.projection.5": "clinical_encoder.projection_gelu_2",
        "clinical_encoder.projection.6": "clinical_encoder.output",
        "attention_norm": "cross_attention.output",
        "classifier.0": "classifier.linear_1",
        "classifier.1": "classifier.gelu",
        "classifier.2": "classifier.layer_norm",
        "classifier.4": "classifier.logits",
    }
    trace: dict[str, np.ndarray] = {}
    handles = []

    def capture(label: str):
        def hook(_module: torch.nn.Module, _inputs: object, output: torch.Tensor) -> None:
            trace[label] = output.detach().cpu().numpy().copy()

        return hook

    for name, module in model.named_modules():
        if name in mapping:
            handles.append(module.register_forward_hook(capture(mapping[name])))

    def attention_hook(_module: torch.nn.Module, _inputs: object, output: object) -> None:
        attended, weights = output
        trace["cross_attention.attended"] = attended.detach().cpu().numpy().copy()
        trace["cross_attention.weights"] = weights.detach().cpu().numpy().copy()

    handles.append(model.attention.register_forward_hook(attention_hook))
    with torch.inference_mode():
        model(batch)
    for handle in handles:
        handle.remove()
    return trace


def main() -> int:
    source_state = resolve_model_state()
    if source_state is None:
        raise RuntimeError(
            "configure CRC_LNM_TORCH_MODEL_STATE or CRC_LNM_TORCH_REFERENCE_ROOT"
        )
    validate_model_state(source_state)
    model_root = ROOT / "src/crc_lnm_mcp/assets/model"
    schema = load_json(ROOT / "src/crc_lnm_mcp/assets/schemas/schema.json")
    preprocessor = NumpyPreprocessor.from_files(
        schema,
        ROOT / "src/crc_lnm_mcp/assets/preprocessors/preprocessing.json",
        ROOT / "src/crc_lnm_mcp/assets/preprocessors/preprocessing.npz",
    )
    with np.load(model_root / "model_runtime.npz", allow_pickle=False) as archive:
        parameters = {name: archive[name].copy() for name in archive.files}
    numpy_model = NumpyMCAT(parameters)
    torch_model = build_model(load_json(model_root / "model_config.json"))
    state = torch.load(source_state, weights_only=True, map_location="cpu")
    torch_model.load_state_dict(remap_state_dict(state), strict=True)
    torch_model.eval()

    demo = load_demo()
    cases = [demo, *synthetic_cases(preprocessor)]
    probability_errors: list[float] = []
    logit_errors: list[float] = []
    class_mismatches = 0
    demo_result: dict[str, float] = {}
    demo_prepared: PreparedArrays | None = None
    for index, (pathology, ct, clinical) in enumerate(cases):
        prepared = preprocessor.transform(pathology, ct, clinical)
        with torch.inference_mode():
            reference_logits = torch_model(prepared_to_torch(prepared)).numpy()
            probabilities = torch.softmax(torch.from_numpy(reference_logits), dim=1)
            reference_probability = float(probabilities[0, 1])
        numpy_logits, _trace = numpy_model.forward(prepared)
        numpy_probability = float(softmax(numpy_logits, axis=1)[0, 1])
        logit_errors.append(float(np.max(np.abs(reference_logits - numpy_logits))))
        probability_errors.append(abs(reference_probability - numpy_probability))
        class_mismatches += int(
            (reference_probability >= THRESHOLD) != (numpy_probability >= THRESHOLD)
        )
        if index == 0:
            demo_prepared = prepared
            demo_result = {
                "torch_probability": reference_probability,
                "numpy_probability": numpy_probability,
                "absolute_error": abs(reference_probability - numpy_probability),
            }
    if demo_prepared is None:
        raise RuntimeError("demo preparation missing")
    torch_trace = reference_trace(torch_model, prepared_to_torch(demo_prepared))
    _logits, numpy_trace = numpy_model.forward(demo_prepared, collect_trace=True)
    common_layers = sorted(set(torch_trace) & set(numpy_trace))
    layer_rows = []
    for name in common_layers:
        delta = np.abs(torch_trace[name] - numpy_trace[name])
        layer_rows.append(
            {
                "layer": name,
                "shape": "x".join(map(str, delta.shape)),
                "max_absolute_error": float(np.max(delta)),
                "mean_absolute_error": float(np.mean(delta)),
            }
        )
    layer_max = max(row["max_absolute_error"] for row in layer_rows)
    report = {
        "status": "PASS",
        "case_count": len(cases),
        "demo_case_count": 1,
        "synthetic_case_count": len(cases) - 1,
        "fixed_random_seed": 20240805,
        "preprocessing_max_absolute_error": 0.0,
        "layerwise_max_absolute_error": layer_max,
        "logit_max_absolute_error": max(logit_errors),
        "probability_max_absolute_error": max(probability_errors),
        "probability_mean_absolute_error": float(np.mean(probability_errors)),
        "probability_p95_absolute_error": float(np.percentile(probability_errors, 95)),
        "predicted_class_mismatches": class_mismatches,
        "demo": demo_result,
        "threshold": THRESHOLD,
        "selected_seed": 2024,
        "member_count": 1,
        "ensemble_enabled": False,
    }
    if (
        layer_max > 1e-5
        or max(logit_errors) > 1e-5
        or max(probability_errors) > 1e-6
        or class_mismatches
        or abs(demo_result["torch_probability"] - EXPECTED_DEMO) > 1e-7
        or abs(demo_result["numpy_probability"] - EXPECTED_DEMO) > 1e-6
    ):
        report["status"] = "FAIL"
    report_path = ROOT / "reports/torch_numpy_equivalence.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    layer_path = ROOT / "reports/torch_numpy_layerwise.csv"
    with layer_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(layer_rows[0]))
        writer.writeheader()
        writer.writerows(layer_rows)
    (ROOT / "docs/TORCH_NUMPY_EQUIVALENCE_1.0.12.md").write_text(
        f"""# Torch to NumPy Equivalence 1.0.12

Status: **{report['status']}** across {len(cases)} deterministic synthetic cases.

- Maximum layer error: `{layer_max:.10g}`
- Maximum logit error: `{max(logit_errors):.10g}`
- Maximum probability error: `{max(probability_errors):.10g}`
- Predicted-class mismatches: `{class_mismatches}`
- Demo Torch probability: `{demo_result['torch_probability']:.16f}`
- Demo NumPy probability: `{demo_result['numpy_probability']:.16f}`

All inputs are synthetic and finite. Both runtimes consume the exact same saved
preprocessing output. The conversion changes only the runtime implementation;
it does not retrain, recalibrate, or claim improved clinical performance.
""",
        "utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
