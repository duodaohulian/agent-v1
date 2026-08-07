# CRC-LNM MCP 1.0.12 Lightweight NumPy Runtime Design

## Objective

Replace the unpublished 1.0.12 default PyTorch runtime with a pure NumPy runtime so a ModelScope `uvx` cold start does not download Torch, NVIDIA, or CUDA packages. Preserve the selected `seed_2024` model, preprocessing, feature order, threshold, six MCP tools, medical output semantics, and lazy single-load behavior.

The original Torch build remains a blocked baseline. The original `model_state.pt` will exist only in `release_1.0.12_torch_runtime_blocked_backup`; it will be excluded from both the final wheel and final source zip.

## Decision

Use a hand-written, model-specific NumPy runtime. ONNX Runtime CPU is not part of the default implementation and is permitted only as a documented fallback if strict Torch-to-NumPy equivalence cannot be achieved without concealing numerical errors. If both routes fail, the release remains blocked.

## Verified Model Structure

The selected model is a fixed, deterministic evaluation graph with 763,842 finite float32 state values across 66 state arrays. Its runtime graph contains:

- five feature encoders built from Linear, exact GELU, LayerNorm, evaluation-mode Dropout, and Linear;
- a clinical encoder using two embeddings, concatenation, Linear, exact GELU, LayerNorm, and evaluation-mode Dropout;
- one fixed 4-head cross-attention block with embedding dimension 128, head dimension 32, query length 1, and context length 5;
- residual addition and LayerNorm;
- a Linear/GELU/LayerNorm/Linear classifier;
- a final two-class Softmax.

Every GELU uses `approximate="none"`. Every LayerNorm uses its saved affine parameters and `eps=1e-5`. Dropout is a no-op in evaluation mode. The graph has no BatchNorm, convolution, sparse operator, dynamic control flow, custom CUDA operator, or runtime network dependency.

## Runtime Components

### `numpy_ops.py`

Implement only the operators used by this model:

- Linear: `x @ weight.T + bias`;
- exact GELU matching PyTorch `approximate="none"`;
- LayerNorm over the saved normalized dimension using the saved weight, bias, and epsilon;
- stable Softmax after subtracting the axis maximum;
- fixed multi-head attention with separate Q/K/V projections obtained from the saved packed projection parameters, scaling by `sqrt(32)`, attention Softmax, head merge, and output projection.

All features and model parameters remain explicitly float32. Integer embedding indices remain int64. The implementation will not grow into a general neural-network framework.

### `numpy_model.py`

Reproduce the archived forward order exactly: pathology encoding, four CT encoders, clinical encoding, fixed cross-attention, residual normalization, fusion, classifier, and logits. Expose an optional trace collector for deterministic layerwise verification without adding test-only state to the production object.

### `numpy_predictor.py`

Use the unchanged `NumpyPreprocessor`, invoke the NumPy model, apply stable two-class Softmax, and return the positive-class probability. It does not adjust or calibrate the result.

### `model_loader.py`

Load the runtime asset lazily with `numpy.load(..., allow_pickle=False)`. Before constructing the predictor, validate the runtime asset checksum and every declared array name, shape, dtype, finite status, per-array checksum, and total parameter count. Preserve current cached-error and retry semantics.

### Conversion and verification scripts

`scripts/convert_torch_to_numpy.py` is a development-only converter. It reads the backed-up seed_2024 state dict with Torch, validates the source checksum, and emits:

- `model_runtime.npz`;
- `model_architecture.json`;
- `model_runtime.sha256`;
- `conversion_manifest.json`.

`scripts/verify_runtime_equivalence.py` runs the original PyTorch reference and new NumPy runtime against deterministic synthetic inputs and emits machine-readable aggregate and layerwise reports. Torch is a conversion/development dependency only and is never a default project dependency.

## Asset and Manifest Contract

The conversion manifest records the source framework, NumPy runtime backend, selected seed, single-member status, source weight checksum, runtime asset checksum, architecture identifier, converter version, threshold, parameter count, array inventory, and research-only status.

The final wheel and source zip contain exactly one runtime model asset, `model_runtime.npz`. They contain no `model_state.pt`, `*.pt`, `*.pth`, `*.ckpt`, Torch module, five-model copy, training resource, ONNX model, or conversion source weight.

The blocked backup preserves the former wheel, sdist, source zip, checksums, cross-platform reports, documentation, regression evidence, and original source weight.

## Lazy Loading and Failure Behavior

Importing the server, MCP initialization, tools/list, model information, case QC, CT preparation, and pathology preparation do not open the runtime NPZ. The first prediction acquires the existing double-check lock and loads the single runtime asset exactly once. Concurrent first predictions share that load, and later predictions reuse it. Report generation consumes the prediction artifact without loading the model again.

Asset or checksum failure is cached as a model initialization failure. It does not terminate the MCP process, does not prevent metadata access, and does not change the five lightweight tool paths. The runtime performs no network access and writes nothing to the installed package directory.

## Output Metadata and Invariants

Model information and prediction output report:

- `package_version=1.0.12`;
- `deployment_profile=single_model_modelscope`;
- `runtime_backend=numpy`;
- `source_framework=pytorch`;
- the original source-model and new runtime-asset checksums;
- `selected_seed=2024`;
- `member_count=1`;
- `ensemble_enabled=false`;
- `threshold=0.3529504342004657`;
- `threshold_recalibrated=false`;
- `research_use_only=true`;
- `independent_test_claim=false`.

The implementation must not claim improved clinical performance. It must preserve feature order, pathology dimension 768, CT dimension 1409 and group dimensions, clinical fields, contract version, predicted class, and the demo probability within the approved numerical tolerance.

## Numerical Equivalence Gate

Compare Torch evaluation/inference mode and NumPy using:

1. every existing synthetic demo/reference case;
2. at least 100 legal, finite, fixed-seed synthetic inputs covering ordinary, zero, negative, and boundary values;
3. one fixed input traced through preprocessing, every Linear output, every normalization output, every activation output, attention, final logits, and probability.

Acceptance criteria are:

- preprocessing maximum absolute error at most `1e-7`;
- intermediate-layer maximum absolute error at most `1e-5`;
- final-logit absolute error at most `1e-5`;
- probability absolute error at most `1e-6`;
- predicted class identical for every case;
- demo probability within `1e-6` of `0.5726384520530701`.

Any tolerance change requires a measured error distribution and identified floating-point cause. Tests may not be loosened to hide an implementation error.

## Dependency and Release Contract

Default dependencies are exact versions of FastMCP, Pydantic, and NumPy only. They exclude Torch, torchvision, torchaudio, ONNX, ONNX Runtime, pandas, scikit-learn, imbalanced-learn, explicit Starlette/Uvicorn/MCP extras, and all NVIDIA/CUDA packages. Conversion dependencies remain isolated from the default install.

Release checks enforce the dependency boundary, absence of forbidden files and imports, exact single runtime asset, checksums and manifest invariants, six registered tools, and a complete prediction in an environment where Torch is absent. README and `modelscope-mcp.json` continue to reference `crc-lnm-medical-agent@1.0.12`.

## Platform and Published-Style Gates

Build one final wheel and install that exact file, never editable, into fresh Python 3.10, Python 3.11, and Python 3.12 environments on Windows and Linux. Every cell must run dependency checks, initialize, tools/list, six independent tool smokes, the complete chain, first and second predictions, probability and load-count regression, arbitrary-CWD import, stdout checks, network checks, and residual-process checks.

Use an isolated empty `UV_CACHE_DIR` for uvx cold-start tests and reuse the same cache for warm-start tests on Windows and Linux. Record dependency resolution/download/install, initialize, tools/list, first and second predictions, RSS, cache growth, site-packages size, and download volume. Linux dependency installation has a ten-minute diagnostic hard limit.

The GitHub Actions workflow builds the wheel once and runs the six OS/Python cells without conversion extras, secrets, publishing, or patient data. It asserts that Torch is absent and uploads JSON evidence. The workflow is authored locally but is not pushed or executed by this task.

## Release Decision

Recommend release only when NumPy equivalence, all six Windows/Linux cells, independent smokes, complete chains, Linux uvx cold/warm starts, dependency exclusions, lazy behavior, runtime size, RSS, and demo regression all pass. Otherwise retain `BLOCKED` and list every unverified item.

This task ends after local conversion, tests, documentation, artifact regeneration, and risk decision. It does not upload to PyPI, push GitHub, or operate ModelScope.
