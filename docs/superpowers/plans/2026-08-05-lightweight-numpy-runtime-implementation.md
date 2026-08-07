# CRC-LNM MCP 1.0.12 Lightweight NumPy Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unpublished PyTorch default runtime with a numerically equivalent, lazy, pure NumPy runtime and pass the complete Windows/Linux/uvx release gate.

**Architecture:** Convert the verified seed_2024 state dict offline into one checksum-inventoried NPZ. At runtime, validate and lazily load that NPZ, execute only the archived fixed MCAT operators in NumPy, and preserve the existing MCP provider and artifact interfaces. Torch remains available only in the blocked backup and development verification environment.

**Tech Stack:** Python 3.10â€?.12, NumPy 2.1.3, PyTorch 2.9.1 for offline reference only, FastMCP 2.14.7, Pydantic 2.13.4, pytest, uv/uvx, PowerShell, Bash.

---

### Task 1: Preserve the blocked Torch baseline

**Files:**
- Create outside workspace: `../release_1.0.12_torch_runtime_blocked_backup/`
- Verify: `dist/*`, `crc-lnm-medical-agent-1.0.12-source.zip`, `RELEASE_CHECKSUMS.sha256`, `docs/CROSS_PLATFORM_RELEASE_GATE_1.0.12.md`, `reports/cross_platform_gate/`, `src/crc_lnm_mcp/assets/model/model_state.pt`

- [ ] Verify the existing full backup remains readable and the workspace is not a Git repository.
- [ ] Create a new exact copy at the requested blocked-backup path without overwriting an existing directory.
- [ ] Compare file count, byte count, wheel hash, source-weight hash, and critical reports.
- [ ] Record the backup evidence before changing production files.

### Task 2: Lock the lightweight release contract with failing tests

**Files:**
- Create: `tests/test_lightweight_runtime_release_contract.py`
- Modify: `tests/test_wheel_contents.py`
- Modify: `tests/test_full_lazy_prediction.py`

- [ ] Add tests requiring default dependencies `fastmcp==2.14.7`, `pydantic==2.13.4`, and `numpy==2.1.3`, with no Torch/ONNX/CUDA family.
- [ ] Add tests requiring `model_runtime.npz`, architecture and conversion manifests, and forbidding PT/PTH/CKPT assets and Torch imports.
- [ ] Add tests requiring lazy NPZ loading, one load attempt, concurrent reuse, cached failure, runtime metadata, and prediction without Torch installed/importable.
- [ ] Run the focused tests and confirm they fail for the missing NumPy runtime and current Torch dependency.

### Task 3: Audit and convert the real seed_2024 state

**Files:**
- Create: `scripts/convert_torch_to_numpy.py`
- Create: `reports/inference_operator_graph.json`
- Create: `docs/INFERENCE_OPERATOR_AUDIT_1.0.12.md`
- Create: `src/crc_lnm_mcp/assets/model/model_runtime.npz`
- Create: `src/crc_lnm_mcp/assets/model/model_architecture.json`
- Create: `src/crc_lnm_mcp/assets/model/model_runtime.sha256`
- Create: `src/crc_lnm_mcp/assets/model/conversion_manifest.json`
- Test: `tests/test_model_conversion.py`

- [ ] Write a failing conversion test asserting the exact 66 state keys, 763,842 parameters, float32/finite arrays, source checksum, and deterministic manifests.
- [ ] Run it and verify the converter is missing.
- [ ] Implement a deterministic converter that loads the backed-up PT file with `weights_only=True`, never mutates tensors, maps every state key to a safe NPZ key, inventories shape/dtype/hash, and writes with no pickle objects.
- [ ] Generate the NPZ and audit outputs, rerun conversion in a temporary directory, and verify equivalent array contents and manifests.
- [ ] Run the conversion tests to green.

### Task 4: Implement and verify model-specific NumPy operators

**Files:**
- Create: `src/crc_lnm_mcp/inference/numpy_ops.py`
- Test: `tests/test_numpy_ops_equivalence.py`

- [ ] Write failing Torch-reference tests for Linear, exact GELU, LayerNorm, stable Softmax, and fixed 4-head attention using deterministic float32 inputs and real saved weights.
- [ ] Confirm failures are due to the missing operator module.
- [ ] Implement minimal float32 operators: `linear`, `gelu_exact`, `layer_norm`, `softmax`, and `multihead_attention`.
- [ ] Compare every operator with Torch using maximum absolute error at most `1e-5` and ensure no production import of Torch.
- [ ] Run focused tests and Ruff to green.

### Task 5: Implement the fixed NumPy model and predictor

**Files:**
- Create: `src/crc_lnm_mcp/inference/numpy_model.py`
- Create: `src/crc_lnm_mcp/inference/numpy_predictor.py`
- Modify: `src/crc_lnm_mcp/inference/predictor.py`
- Test: `tests/test_numpy_model_equivalence.py`

- [ ] Write failing tests for every encoder, clinical embedding path, attention output, fused classifier logits, probability, and optional trace names.
- [ ] Use one real demo input and deterministic synthetic arrays to prove the tests fail before implementation.
- [ ] Implement the exact archived forward order with model-specific parameter lookup and no general framework abstraction.
- [ ] Make `predictor.py` expose only NumPy runtime types or remove its Torch implementation after reference logic is safely isolated in development scripts/tests.
- [ ] Verify layer/logit/probability thresholds and exact predicted class.

### Task 6: Replace the loader while preserving lazy and failure semantics

**Files:**
- Modify: `src/crc_lnm_mcp/inference/model_loader.py`
- Modify: `src/crc_lnm_mcp/services/prediction_service.py`
- Modify: `src/crc_lnm_mcp/assets/model/deployment_manifest.json`
- Test: `tests/test_numpy_runtime_loader.py`

- [ ] Write failing tests for checksum validation, exact array inventory, shape, dtype, finite values, per-array hashes, parameter count, `allow_pickle=False`, and one lazy load under concurrency.
- [ ] Implement the loader against package resources without writing extracted files to the installation directory.
- [ ] Preserve cached initialization failures and availability of the five lightweight tools.
- [ ] Update model version fields to source-model/runtime-asset metadata without changing medical outputs.
- [ ] Run lazy/concurrency/error tests to green while blocking all Torch imports.

### Task 7: Update contracts, metadata, dependencies, and release checks

**Files:**
- Modify: `src/crc_lnm_mcp/contracts/model_info.py`
- Modify: `src/crc_lnm_mcp/contracts/prediction.py`
- Modify: `src/crc_lnm_mcp/services/metadata_service.py`
- Modify: `pyproject.toml`
- Modify: `MANIFEST.in`
- Modify: `scripts/check_release.py`
- Modify: `scripts/inspect_wheel.py`
- Modify: `README.md`
- Test: `tests/test_lightweight_runtime_release_contract.py`

- [ ] Write/extend failing assertions for `runtime_backend=numpy`, source/runtime hashes, exact default dependencies, forbidden packages/files/imports, single runtime model, and unchanged 1.0.12 ModelScope command.
- [ ] Update the contracts and metadata with only additive runtime provenance fields compatible with the approved public behavior.
- [ ] Remove Torch from defaults and package data; keep conversion tooling outside wheel contents.
- [ ] Make release checks install/predict successfully when Torch import is blocked.
- [ ] Run focused contract and release tests to green.

### Task 8: Produce strict Torch-to-NumPy equivalence evidence

**Files:**
- Create: `scripts/verify_runtime_equivalence.py`
- Create: `reports/torch_numpy_equivalence.json`
- Create: `reports/torch_numpy_layerwise.csv`
- Create: `docs/TORCH_NUMPY_EQUIVALENCE_1.0.12.md`
- Test: `tests/test_runtime_equivalence_report.py`

- [ ] Write a failing report-contract test for all demos, at least 100 deterministic legal inputs, required edge classes, layer traces, errors, class agreement, and demo probability.
- [ ] Implement the verifier using the backed-up Torch source and final NumPy runtime through identical preprocessing.
- [ ] Run it with fixed seeds and capture maximum/mean/percentile errors plus the worst case/layer.
- [ ] Require preprocessing `<=1e-7`, layer/logit `<=1e-5`, probability `<=1e-6`, and complete class agreement.
- [ ] Keep BLOCKED and stop NumPy release work if any unexplained error exceeds the gate.

### Task 9: Rebuild and audit final artifacts

**Files:**
- Modify: `scripts/build_release_artifacts.py`
- Modify: `scripts/release_verify_full.ps1`
- Modify: `scripts/release_verify_full_linux.sh`
- Regenerate: `dist/*.whl`, `dist/*.tar.gz`, source zip, `RELEASE_CHECKSUMS.sha256`

- [ ] Archive the former blocked dist without overwriting it.
- [ ] Remove the original PT file from the working source only after conversion and equivalence evidence pass.
- [ ] Build wheel/sdist, run `twine check`, inspect the wheel, and assert exactly one NPZ runtime asset and no Torch/PT/training resources.
- [ ] Generate a source zip that also excludes the original PT file while retaining conversion scripts and reports.
- [ ] Record the new size and SHA-256; reject the old `88974a...d4c4` hash.

### Task 10: Execute Windows Python 3.10, Python 3.11, and Python 3.12 gates

**Files:**
- Create reports under: `reports/lightweight_cross_platform_gate/windows-py*/`

- [ ] Create three fresh non-editable environments and install the exact final wheel.
- [ ] Assert Torch/NVIDIA/CUDA distributions and imports are absent.
- [ ] Run dependency checks, arbitrary-CWD import, six independent smokes, full chain, first/second predictions, probability/load invariants, network checks, stdout checks, RSS, and residual-process checks.
- [ ] Clean exact temporary environments when policy permits and preserve JSON evidence.

### Task 11: Execute Linux and uvx cold/warm gates

**Files:**
- Modify: `scripts/audit_linux_uvx_cold_start.sh`
- Create reports under: `reports/lightweight_cross_platform_gate/linux-py*/`
- Create: `reports/lightweight_uvx_cold_start.json`
- Create: `reports/lightweight_uvx_warm_start.json`

- [ ] Use project-specific empty cache directories and the existing WSL Python 3.10/3.11/3.12 runtimes.
- [ ] Separately time dependency resolution, download, installation, initialize, tools/list, lightweight tools, first/second predictions, report generation, RSS, cache delta, installed bytes, and downloads.
- [ ] Enforce a ten-minute dependency-install diagnostic limit and record the exact package/network stage on failure.
- [ ] Run Linux three-version wheel-only matrices and Linux/Windows local-wheel uvx cold/warm published-style smokes.
- [ ] Compare cold-install improvement against the >1804-second/897-MB blocked Torch baseline and verify no residual processes.

### Task 12: Update CI, final documentation, and release decision

**Files:**
- Modify: `.github/workflows/release-matrix-1.0.12.yml`
- Create: `docs/LIGHTWEIGHT_RUNTIME_RELEASE_GATE_1.0.12.md`
- Modify: `docs/MODELSCOPE_RUNTIME_RISK_1.0.12.md`
- Create: `docs/DEPENDENCY_AUDIT_1.0.12.md`
- Create: `docs/ROLLBACK_1.0.12.md`

- [ ] Update the six-cell workflow to install one wheel, assert Torch absence, run every smoke/regression, and upload JSON artifacts without secrets or publication.
- [ ] Run YAML/PowerShell/Bash syntax checks, Ruff, full pytest, release checks, artifact checksums, and residual-process checks fresh.
- [ ] Write the Aâ€“V report using observed values only and enumerate every unverified hosted/ModelScope item.
- [ ] Recommend release only if every locally required NumPy, Windows, Linux, and uvx gate passes; otherwise retain BLOCKED.
- [ ] Stop without uploading PyPI, pushing GitHub, or operating ModelScope.
