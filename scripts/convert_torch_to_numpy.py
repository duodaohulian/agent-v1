"""Convert the verified seed_2024 PyTorch state into a deterministic safe NPZ."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch_reference_paths import resolve_model_state

from crc_lnm_mcp.inference.checksums import canonical_json_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "src/crc_lnm_mcp/assets/model"
SOURCE_SHA256 = "40e9fbed0da4fa915626e5c0bc6874a10a9129448271614fd011d31c46deeb17"
PARAMETER_COUNT = 763842
CONVERTER_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_key(source_key: str) -> str:
    return source_key.replace(".", "__")


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name in sorted(arrays):
            payload = io.BytesIO()
            np.lib.format.write_array(payload, arrays[name], allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload.getvalue())


def architecture_document() -> dict[str, Any]:
    return {
        "architecture": "attention_path_ct_clinical",
        "runtime_backend": "numpy",
        "dtype": "float32",
        "parameter_count": PARAMETER_COUNT,
        "hidden_dim": 128,
        "attention": {
            "embed_dim": 128,
            "num_heads": 4,
            "head_dim": 32,
            "query_length": 1,
            "context_length": 5,
            "dropout_eval": 0.0,
        },
        "gelu_approximate": "none",
        "layer_norm_eps": 1e-5,
        "dropout_eval_no_op": True,
        "input_shapes": {
            "pathology": [1, 768],
            "ct_shape": [1, 14],
            "ct_original": [1, 93],
            "ct_wavelet": [1, 744],
            "ct_transformed": [1, 558],
            "age": [1, 1],
            "male": [1, 1],
            "type_index": [1],
            "t_stage_index": [1],
        },
    }


def operator_graph(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "architecture": "attention_path_ct_clinical",
        "fixed_forward_graph": True,
        "dynamic_control_flow": False,
        "custom_cuda_operators": False,
        "batch_norm": False,
        "dropout_eval_no_op": True,
        "operators": [
            "Linear",
            "GELU(approximate=none)",
            "LayerNorm(eps=1e-5)",
            "Embedding",
            "concatenate",
            "stack",
            "MultiheadAttention(4 heads, head_dim=32)",
            "residual_add",
            "Softmax",
        ],
        "parameter_count": PARAMETER_COUNT,
        "state_array_count": len(inventory),
        "arrays": inventory,
        "numpy_equivalent": True,
    }


def convert(source: Path, output_dir: Path, *, write_audit: bool = False) -> dict[str, Any]:
    source = source.resolve()
    if sha256_file(source) != SOURCE_SHA256:
        raise RuntimeError("source model checksum mismatch")
    state = torch.load(source, weights_only=True, map_location="cpu")
    if not isinstance(state, dict) or len(state) != 66:
        raise RuntimeError("source state_dict inventory mismatch")
    arrays: dict[str, np.ndarray] = {}
    inventory: list[dict[str, Any]] = []
    for source_name in sorted(state):
        tensor = state[source_name]
        if not isinstance(source_name, str) or not isinstance(tensor, torch.Tensor):
            raise RuntimeError("source state_dict is invalid")
        array = np.ascontiguousarray(tensor.detach().cpu().numpy(), dtype=np.float32)
        if not np.isfinite(array).all():
            raise RuntimeError(f"source array is non-finite: {source_name}")
        name = asset_key(source_name)
        arrays[name] = array
        inventory.append(
            {
                "source_key": source_name,
                "asset_key": name,
                "shape": list(array.shape),
                "dtype": str(array.dtype),
                "parameter_count": int(array.size),
                "sha256": hashlib.sha256(array.tobytes(order="C")).hexdigest(),
            }
        )
    if sum(array.size for array in arrays.values()) != PARAMETER_COUNT:
        raise RuntimeError("source parameter count mismatch")
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_path = output_dir / "model_runtime.npz"
    write_deterministic_npz(runtime_path, arrays)
    runtime_sha256 = sha256_file(runtime_path)
    architecture = architecture_document()
    manifest = {
        "conversion_script_version": CONVERTER_VERSION,
        "source_framework": "pytorch",
        "runtime_framework": "numpy",
        "selected_seed": 2024,
        "member_count": 1,
        "ensemble_enabled": False,
        "source_weight_sha256": SOURCE_SHA256,
        "runtime_asset_sha256": runtime_sha256,
        "runtime_asset_file": "model_runtime.npz",
        "model_architecture": "attention_path_ct_clinical",
        "parameter_count": PARAMETER_COUNT,
        "array_count": len(inventory),
        "arrays": inventory,
        "threshold": 0.3529504342004657,
        "threshold_recalibrated": False,
        "research_use_only": True,
    }
    write_json(output_dir / "model_architecture.json", architecture)
    conversion_path = output_dir / "conversion_manifest.json"
    write_json(conversion_path, manifest)
    deployment_path = output_dir / "deployment_manifest.json"
    if deployment_path.is_file():
        deployment = json.loads(deployment_path.read_text(encoding="utf-8"))
        deployment["conversion_manifest_sha256"] = canonical_json_sha256(conversion_path)
        deployment["model_architecture_sha256"] = canonical_json_sha256(
            output_dir / "model_architecture.json"
        )
        write_json(deployment_path, deployment)
    (output_dir / "model_runtime.sha256").write_text(runtime_sha256 + "\n", "ascii")
    if write_audit:
        graph = operator_graph(inventory)
        write_json(ROOT / "reports/inference_operator_graph.json", graph)
        (ROOT / "docs/INFERENCE_OPERATOR_AUDIT_1.0.12.md").write_text(
            """# Inference Operator Audit 1.0.12

The verified seed_2024 model is a fixed float32 evaluation graph with 763,842
parameters across 66 state arrays. It contains Linear, exact GELU
(`approximate=\"none\"`), LayerNorm (`eps=1e-5`), Embedding, concatenation,
stacking, a fixed four-head attention block, residual addition, and Softmax.

Evaluation-mode Dropout is a no-op. The model contains no BatchNorm,
convolution, sparse operation, dynamic control flow, custom operation, or CUDA
requirement. The attention dimensions are fixed: embedding 128, four heads,
head dimension 32, query length 1, and context length 5. The saved packed Q/K/V
and output projection weights are sufficient for a complete NumPy equivalent.

The full state inventory, shapes, dtypes, checksums, and parameter counts are in
`reports/inference_operator_graph.json`. This audit supports the pure NumPy
runtime decision; ONNX Runtime is not required.
""",
            encoding="utf-8",
        )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write-audit", action="store_true")
    args = parser.parse_args()
    source = args.source or resolve_model_state()
    if source is None:
        parser.error(
            "configure CRC_LNM_TORCH_MODEL_STATE or CRC_LNM_TORCH_REFERENCE_ROOT, "
            "or pass --source"
        )
    manifest = convert(source, args.output_dir, write_audit=args.write_audit)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
