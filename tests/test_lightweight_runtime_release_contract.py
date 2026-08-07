from __future__ import annotations

import ast
import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/crc_lnm_mcp/assets/model"
EXPECTED_DEPENDENCIES = [
    "fastmcp==2.14.7",
    "pydantic==2.13.4",
    "numpy==2.1.3",
]


def test_default_dependencies_are_lightweight_and_exact() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"]
    assert project["dependencies"] == EXPECTED_DEPENDENCIES
    normalized = "\n".join(project["dependencies"]).lower()
    for forbidden in ("torch", "onnx", "nvidia", "cuda"):
        assert forbidden not in normalized


def test_source_model_is_replaced_by_one_numpy_runtime_asset() -> None:
    assert not (MODEL / "model_state.pt").exists()
    assert sorted(path.name for path in MODEL.glob("*.npz")) == ["model_runtime.npz"]
    for name in (
        "model_architecture.json",
        "model_runtime.sha256",
        "conversion_manifest.json",
    ):
        assert (MODEL / name).is_file()


def test_runtime_python_sources_never_import_torch() -> None:
    offenders: list[str] = []
    package = ROOT / "src/crc_lnm_mcp"
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name == "torch" or alias.name.startswith("torch.") for alias in node.names
            ):
                offenders.append(path.relative_to(package).as_posix())
            if isinstance(node, ast.ImportFrom) and node.module and (
                node.module == "torch" or node.module.startswith("torch.")
            ):
                offenders.append(path.relative_to(package).as_posix())
    assert sorted(set(offenders)) == []


def test_conversion_manifest_locks_medical_invariants() -> None:
    manifest = json.loads((MODEL / "conversion_manifest.json").read_text("utf-8"))
    assert manifest["source_framework"] == "pytorch"
    assert manifest["runtime_framework"] == "numpy"
    assert manifest["selected_seed"] == 2024
    assert manifest["member_count"] == 1
    assert manifest["ensemble_enabled"] is False
    assert manifest["source_weight_sha256"] == (
        "40e9fbed0da4fa915626e5c0bc6874a10a9129448271614fd011d31c46deeb17"
    )
    assert manifest["parameter_count"] == 763842
    assert manifest["threshold"] == 0.3529504342004657
    assert manifest["research_use_only"] is True
