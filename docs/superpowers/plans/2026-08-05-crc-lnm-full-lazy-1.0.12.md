# CRC-LNM Full Lazy 1.0.12 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore exactly six CRC-LNM medical MCP tools in the 1.0.11 STDIO shell and ship a checksum-verified, lazily loaded single-model 1.0.12 wheel.

**Architecture:** A lightweight FastMCP server registers six independent adapters backed by metadata, case/feature, and prediction providers. Only the prediction provider imports Torch and loads the one model selected by demo-to-ensemble probability MAE; all other work remains metadata- or artifact-only.

**Tech Stack:** Python 3.10-3.12, FastMCP 2.14.7, Pydantic 2.13.4, NumPy, CPU Torch, Pytest, MCP STDIO client, setuptools/build/Twine.

---

## File Map

- `src/crc_lnm_mcp/server.py`: lazy FastMCP construction, six registrations, STDIO entry.
- `src/crc_lnm_mcp/runtime.py`: metadata, case/feature, and prediction provider ownership.
- `src/crc_lnm_mcp/settings.py`: bounded package-resource settings only.
- `src/crc_lnm_mcp/errors.py`: stable structured runtime failures.
- `src/crc_lnm_mcp/contracts/*.py`: focused request/response schemas.
- `src/crc_lnm_mcp/tools/*.py`: one adapter per formal MCP tool.
- `src/crc_lnm_mcp/services/*.py`: transport-independent business services.
- `src/crc_lnm_mcp/inference/*.py`: NumPy preprocessing and delayed Torch predictor.
- `src/crc_lnm_mcp/assets/`: one model, metadata, preprocessor, schema, cases, template.
- `tests/test_full_lazy_*.py`: static, unit, concurrency, safety, wheel, and STDIO tests.
- `scripts/smoke_tool_*.py`: six isolated protocol smokes and one complete pipeline.
- `docs/*.md`, `reports/*`: required audit, selection, regression, dependency, and performance evidence.

### Task 1: Baseline Audit and Evidence-Based Model Selection

**Files:**
- Create: `tests/test_full_lazy_selection.py`
- Create: `scripts/select_single_model.py`
- Create: `docs/FULL_RUNTIME_BASELINE_AUDIT.md`
- Create: `docs/SINGLE_MODEL_SELECTION.md`
- Create: `reports/single_model_selection.json`
- Create: `reports/single_model_comparison.csv`
- Create: `reports/single_model_regression.json`
- Create: `docs/SINGLE_VS_ENSEMBLE_REGRESSION.md`

- [ ] **Step 1: Write failing selection tests**

```python
def test_selection_uses_all_five_members_and_demo_only(selection_report):
    assert [row["seed"] for row in selection_report["candidates"]] == [2024, 3407, 5280, 7319, 9021]
    assert selection_report["selection_dataset"] == "demo_case_001"
    assert selection_report["selection_method"] == "minimum_mae_to_ensemble"

def test_selected_model_is_deterministic(selection_report):
    selected = [row for row in selection_report["candidates"] if row["selected"]]
    assert len(selected) == 1
    assert selected[0]["mae_to_ensemble"] == min(row["mae_to_ensemble"] for row in selection_report["candidates"])
```

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_selection.py -q`
Expected: FAIL because selection reports do not exist.

- [ ] **Step 3: Implement the bounded benchmark**

Load the existing five members and `demo/cases/demo_case_001`, measure ensemble and per-member
probabilities, load/inference seconds, process RSS, hashes, and deterministic tie breakers. Do
not read `data/release_case_package_groups.jsonl` and do not use a label.

- [ ] **Step 4: Generate reports and verify GREEN**

Run: `python scripts/select_single_model.py` using the existing Anaconda Python 3.13 medical
environment, which already contains the legacy Torch/NumPy/pandas stack. The script is a
read-only development benchmark and is not the 1.0.12 release interpreter.
Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_selection.py -q`
Expected: reports are generated and all selection tests pass.

### Task 2: Stage A Exact Six-Tool Registration

**Files:**
- Create: `tests/test_full_lazy_registration.py`
- Create: `src/crc_lnm_mcp/contracts/common.py`
- Create: `src/crc_lnm_mcp/contracts/model_info.py`
- Create: `src/crc_lnm_mcp/contracts/case_qc.py`
- Create: `src/crc_lnm_mcp/contracts/ct_features.py`
- Create: `src/crc_lnm_mcp/contracts/pathology_features.py`
- Create: `src/crc_lnm_mcp/contracts/prediction.py`
- Create: `src/crc_lnm_mcp/contracts/report.py`
- Create: `src/crc_lnm_mcp/tools/get_model_info.py`
- Create: `src/crc_lnm_mcp/tools/case_data_qc.py`
- Create: `src/crc_lnm_mcp/tools/prepare_ct_features.py`
- Create: `src/crc_lnm_mcp/tools/prepare_pathology_features.py`
- Create: `src/crc_lnm_mcp/tools/predict_multimodal.py`
- Create: `src/crc_lnm_mcp/tools/generate_report.py`
- Modify: `src/crc_lnm_mcp/server.py`

- [ ] **Step 1: Write failing registration/import tests**

```python
EXPECTED = {
    "crc_lnm_get_model_info", "crc_lnm_case_data_qc",
    "crc_lnm_prepare_ct_features", "crc_lnm_prepare_pathology_features",
    "crc_lnm_predict_multimodal", "crc_lnm_generate_report",
}

def test_exact_six_tools():
    assert set(asyncio.run(server.get_mcp().get_tools())) == EXPECTED

def test_import_server_without_torch():
    assert "torch" not in sys.modules
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_registration.py -q`
Expected: FAIL because only the two canary tools exist.

- [ ] **Step 3: Add focused schemas and placeholder adapters**

Port the frozen 1.1.0 request/response fields into focused modules, change real deployment
semantics to `member_count=1` and `ensemble_enabled=false`, and register six adapters whose
business call initially returns structured `SERVICE_UNAVAILABLE` without loading medical
dependencies.

- [ ] **Step 4: Verify GREEN and no Torch import**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_registration.py -q`
Expected: exact six tools and no Torch/model/case preload.

### Task 3: Stage B Metadata Provider and Model Info

**Files:**
- Create: `tests/test_full_lazy_metadata.py`
- Create: `src/crc_lnm_mcp/settings.py`
- Create: `src/crc_lnm_mcp/runtime.py`
- Create: `src/crc_lnm_mcp/services/metadata_service.py`
- Create: `src/crc_lnm_mcp/assets/model/deployment_manifest.json`
- Copy selected lightweight schema/preprocessor metadata under `src/crc_lnm_mcp/assets/`.
- Modify: `src/crc_lnm_mcp/tools/get_model_info.py`

- [ ] **Step 1: Write failing metadata tests**

```python
def test_model_info_without_torch(runtime):
    data = runtime.metadata.get_model_info()
    assert data["member_count"] == 1
    assert data["ensemble_enabled"] is False
    assert data["selected_model_id"]
    assert "torch" not in sys.modules
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_metadata.py -q`
Expected: FAIL because metadata provider and manifest are absent.

- [ ] **Step 3: Implement bounded JSON metadata reads**

Resolve resources with `importlib.resources`, reject oversized/malformed JSON, expose no
absolute path, and make the manifest the only selected-model identifier source.

- [ ] **Step 4: Verify GREEN**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_metadata.py tests/test_full_lazy_registration.py -q`
Expected: model info succeeds with Torch import blocked.

### Task 4: Stage C Indexed Case Repository, Artifacts, and QC

**Files:**
- Create: `tests/test_full_lazy_case_qc.py`
- Create: `src/crc_lnm_mcp/services/case_service.py`
- Create: `src/crc_lnm_mcp/services/artifact_service.py`
- Create: `src/crc_lnm_mcp/assets/cases/demo_cases.jsonl`
- Modify: `src/crc_lnm_mcp/runtime.py`
- Modify: `src/crc_lnm_mcp/tools/case_data_qc.py`

- [ ] **Step 1: Write failing lazy-index and safety tests**

```python
def test_case_qc_without_torch(case_provider):
    assert case_provider.indexed_record_count == 0
    result = case_provider.case_data_qc("demo_case_001", request_id=REQUEST_ID, trace_id=TRACE_ID)
    assert result.passed is True
    assert case_provider.indexed_record_count == 1
    assert "torch" not in sys.modules

@pytest.mark.parametrize("value", ["../manifest", "<TEMP_WORKSPACE>\\secret", "/tmp/case", "demo/case"])
def test_no_arbitrary_path(case_provider, value):
    with pytest.raises(ValueError):
        case_provider.case_data_qc(value, request_id=REQUEST_ID, trace_id=TRACE_ID)
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_case_qc.py -q`
Expected: FAIL because indexed repository and artifacts are absent.

- [ ] **Step 3: Implement byte-offset index and bounded in-memory artifacts**

Build the index only on first case call, validate manifest checksums, privacy fields,
modalities, dimensions, and allowlisted references; never accept user paths or write package
resources.

- [ ] **Step 4: Verify GREEN**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_case_qc.py tests/test_full_lazy_metadata.py -q`
Expected: QC passes, traversal is rejected, and Torch remains absent.

### Task 5: Stages D and E CT/Pathology Feature Preparation

**Files:**
- Create: `tests/test_full_lazy_features.py`
- Create: `src/crc_lnm_mcp/services/ct_feature_service.py`
- Create: `src/crc_lnm_mcp/services/pathology_feature_service.py`
- Modify: `src/crc_lnm_mcp/tools/prepare_ct_features.py`
- Modify: `src/crc_lnm_mcp/tools/prepare_pathology_features.py`

- [ ] **Step 1: Write failing feature tests**

```python
def test_feature_dimensions_and_order(workflow):
    qc = workflow.qc()
    ct = workflow.ct(qc.artifact.artifact_id)
    pathology = workflow.pathology(qc.artifact.artifact_id)
    assert ct.feature_count == 1409
    assert ct.group_counts.model_dump() == {"shape": 14, "original": 93, "wavelet": 744, "transformed": 558}
    assert pathology.feature_count == 768
    assert "torch" not in sys.modules
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_features.py -q`
Expected: FAIL because feature services are absent.

- [ ] **Step 3: Implement exact-key, finite-value, order, and artifact validation**

Retain vectors only inside bounded artifacts, return summaries and hashes, enforce same-case,
same-trace, stage order, dimensions, and schema order.

- [ ] **Step 4: Verify GREEN**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_features.py tests/test_full_lazy_case_qc.py -q`
Expected: CT and pathology pass independently without Torch.

### Task 6: Stage F Single-Model Lazy Prediction

**Files:**
- Create: `tests/test_full_lazy_prediction.py`
- Create: `src/crc_lnm_mcp/inference/preprocessing.py`
- Create: `src/crc_lnm_mcp/inference/model_loader.py`
- Create: `src/crc_lnm_mcp/inference/predictor.py`
- Create: `src/crc_lnm_mcp/services/prediction_service.py`
- Copy: selected `model_config.json` and `model_state.pt` into `src/crc_lnm_mcp/assets/model/`.
- Copy/export: checksum-locked NumPy preprocessing assets.
- Modify: `src/crc_lnm_mcp/runtime.py`
- Modify: `src/crc_lnm_mcp/tools/predict_multimodal.py`

- [ ] **Step 1: Write failing lazy/concurrency/checksum tests**

```python
def test_prediction_triggers_torch_and_reuses_one_model(prepared_prediction):
    provider, request = prepared_prediction
    assert provider.load_count == 0
    first = provider.predict(request)
    second = provider.predict(request)
    assert provider.load_count == 1
    assert provider.prediction_count == 2
    assert first.member_count == second.member_count == 1
    assert first.ensemble_enabled is second.ensemble_enabled is False

def test_concurrent_first_prediction_loads_once(prepared_prediction):
    provider, request = prepared_prediction
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: provider.predict(request), range(4)))
    assert provider.load_count == 1
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_prediction.py -q`
Expected: FAIL because prediction provider is absent.

- [ ] **Step 3: Implement NumPy transform equivalence before model code**

Add a test comparing legacy and NumPy preprocessing arrays at strict tolerance, run it RED,
then implement the minimal transform and run it GREEN.

- [ ] **Step 4: Implement locked delayed load and prediction**

Inside the lock import Torch and the model class, verify manifest/model/preprocessor hashes,
load `weights_only=True` on CPU, call `eval()` and `torch.inference_mode()`, retain one
predictor, record diagnostics, and convert failure to structured `BUNDLE_INTEGRITY_FAILURE`
or `INFERENCE_FAILURE` without killing the server.

- [ ] **Step 5: Verify GREEN and two-call reuse**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_prediction.py tests/test_full_lazy_features.py -q`
Expected: one load, one instance, member count one, ensemble false, stable regression values.

### Task 7: Stage G Artifact-Only Report

**Files:**
- Create: `tests/test_full_lazy_report.py`
- Create: `src/crc_lnm_mcp/services/report_service.py`
- Modify: `src/crc_lnm_mcp/tools/generate_report.py`
- Copy or replace: `src/crc_lnm_mcp/assets/report.html.j2`

- [ ] **Step 1: Write failing report isolation test**

```python
def test_report_from_artifact_without_torch(report_fixture, monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", None)
    response = report_fixture.generate()
    assert response.report_format == "html"
    assert response.safety_statement
    assert report_fixture.prediction_provider.load_count == 0
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_report.py -q`
Expected: FAIL because report service is absent.

- [ ] **Step 3: Implement escaped deterministic report generation**

Read only QC and prediction artifacts, preserve the fixed six sections and research-only
language, store the HTML as a bounded report artifact, and never access prediction provider.

- [ ] **Step 4: Verify GREEN**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_report.py tests/test_full_lazy_prediction.py -q`
Expected: artifact-only report succeeds without model loading.

### Task 8: Independent and Complete STDIO Smokes

**Files:**
- Create: `scripts/smoke_common.py`
- Create: `scripts/smoke_tool_01_model_info.py`
- Create: `scripts/smoke_tool_02_case_qc.py`
- Create: `scripts/smoke_tool_03_ct_features.py`
- Create: `scripts/smoke_tool_04_pathology_features.py`
- Create: `scripts/smoke_tool_05_prediction.py`
- Create: `scripts/smoke_tool_06_report.py`
- Create: `scripts/smoke_all_six_tools.py`
- Create: `tests/test_full_lazy_stdio.py`
- Create: `reports/six_tool_smoke_results.json`

- [ ] **Step 1: Write failing smoke contract tests**

Assert each script launches the formal console command, initializes, lists exactly six tools,
calls only its target and minimal prerequisites, shuts down, reports timings, rejects stdout
pollution, and reports zero leaked processes/CWD files/network violations.

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_stdio.py -q`
Expected: FAIL because seven smoke scripts are absent.

- [ ] **Step 3: Implement shared MCP client lifecycle and scripts**

Reuse one strict subprocess client helper, UUID-stable request builders, bounded timeouts,
stderr capture, process cleanup, temporary-directory inventory, and structured JSON output.

- [ ] **Step 4: Run six isolated smokes in order, then the complete pipeline**

Run each `scripts/smoke_tool_0N_*.py`; stop on the first failure. Then run
`scripts/smoke_all_six_tools.py --output reports/six_tool_smoke_results.json`.
Expected: every script reports PASS with measured timings.

### Task 9: Packaging, Release Verification, and Final Documentation

**Files:**
- Create: `tests/test_full_lazy_release.py`
- Modify: `pyproject.toml`
- Modify: `MANIFEST.in`
- Modify: `modelscope-mcp.json`
- Modify: `README.md`
- Modify: `scripts/check_release.py`
- Modify: `scripts/inspect_wheel.py`
- Create: `scripts/release_verify_full.ps1`
- Create: all remaining requested `docs/*.md` release documents.
- Create: `dist/crc_lnm_medical_agent-1.0.12-py3-none-any.whl`
- Create: `dist/crc_lnm_medical_agent-1.0.12.tar.gz`
- Create: `crc-lnm-medical-agent-1.0.12-source.zip`
- Create: `RELEASE_CHECKSUMS_1.0.12.sha256`

- [ ] **Step 1: Write failing release closure tests**

```python
def test_package_version_1_0_12(pyproject):
    assert pyproject["project"]["version"] == "1.0.12"

def test_only_one_model_weight_in_wheel(wheel_names):
    assert len([name for name in wheel_names if name.endswith("model_state.pt")]) == 1

def test_modelscope_json_exact_version(config):
    assert config == {"mcpServers": {"crc-lnm-medical-agent": {"command": "uvx", "args": ["crc-lnm-medical-agent@1.0.12"]}}}
```

- [ ] **Step 2: Verify RED**

Run: `.venv-release\Scripts\python.exe -m pytest tests/test_full_lazy_release.py -q`
Expected: FAIL on version, config, package data, and absent artifacts.

- [ ] **Step 3: Update packaging and dependency surface**

Set version 1.0.12, include only `crc_lnm_mcp`, one model and required assets, declare the
audited direct runtime dependencies, keep one console script, and make README formal config
byte-equivalent in meaning to root JSON.

- [ ] **Step 4: Run full source quality suite**

Run: `.venv-release\Scripts\python.exe -m pytest -q`
Run: `.venv-release\Scripts\ruff.exe check src tests scripts`
Run: `.venv-release\Scripts\mypy.exe src/crc_lnm_mcp`
Expected: all applicable checks pass with no stdout warnings.

- [ ] **Step 5: Clean build and inspect artifacts**

Run: `scripts\release_verify_full.ps1`
Expected: build, Twine, release checks, wheel inventory, wheel-only arbitrary-CWD install,
six isolated smokes, full smoke, checksum generation, and source archive all pass.

- [ ] **Step 6: Complete evidence documents with measured values**

Write contract diff, dependency audit, performance report, release/deployment guide,
rollback guide, model selection limitations, regression deltas, Python matrix, wheel sizes,
model count, load/reuse timings, RSS, stdout, process, network, and unverified-risk evidence.

- [ ] **Step 7: Final independent verification**

Recompute artifact SHA-256, inspect the final wheel directly, install it into a new temporary
environment, run the complete STDIO pipeline from an arbitrary CWD, and confirm no external
publish, Git, or ModelScope action occurred.
