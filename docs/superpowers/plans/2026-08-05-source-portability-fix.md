# Source Package Portability Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the 1.0.12 source release relocatable with and without protected Torch reference assets, rebuild and verify every artifact, then commit and push the existing release branch.

**Architecture:** Centralize protected-reference discovery in `tests/conftest.py` using explicit environment variables only. Keep runtime tests independent of Torch assets, make conversion-only tests skip with one exact reason when the reference is absent, and make the source archive explicitly include required dotfiles while rejecting protected weights and developer paths.

**Tech Stack:** Python 3.12, pytest, Ruff, NumPy, optional development-only PyTorch, setuptools/build, PowerShell, Bash, Git.

---

### Task 1: Preserve and reproduce

**Files:**
- Create externally: `../release_1.0.12_before_source_portability_fix/`
- Inspect: `tests/test_model_conversion.py`
- Inspect: `tests/test_numpy_model_equivalence.py`
- Inspect: `tests/test_release_closure.py`

- [ ] Record old artifact hashes, Git HEAD, branch, and status.
- [ ] Reproduce Ruff and pytest failures in the release Python 3.12 environment.
- [ ] Confirm failures arise from import order, repository-parent reference discovery, and missing `.gitignore`.

### Task 2: Add explicit protected-reference fixtures

**Files:**
- Create: `tests/conftest.py`
- Modify: `tests/test_model_conversion.py`
- Modify: `tests/test_numpy_model_equivalence.py`
- Test: `tests/test_source_portability.py`

- [ ] Add failing tests proving repository-parent discovery is forbidden and both explicit environment variables resolve correctly.
- [ ] Run the focused tests and confirm the expected failures.
- [ ] Implement fixtures for `CRC_LNM_TORCH_MODEL_STATE` and `CRC_LNM_TORCH_REFERENCE_ROOT`, source SHA verification, and the exact missing-reference skip reason.
- [ ] Inject fixtures into conversion-only tests; leave runtime asset and report-integrity tests unconditional.
- [ ] Run focused tests with an explicit protected reference and with both variables removed.

### Task 3: Add release hygiene and archive contracts

**Files:**
- Create: `.gitignore`
- Modify: `tests/test_release_closure.py`
- Modify: `scripts/build_release_artifacts.py`
- Modify: `scripts/check_release.py`
- Test: `tests/test_source_portability.py`

- [ ] Add failing tests for `.gitignore`, required source-zip members, forbidden weights/paths, and CI without Torch.
- [ ] Run the focused tests and confirm expected failures.
- [ ] Add the specified `.gitignore` rules without excluding `model_runtime.npz`, docs, reports, `.github`, or ModelScope configuration.
- [ ] Explicitly include `.gitignore`, `.github`, release configuration, source, tests, scripts, docs, and reports in the archive; exclude caches, environments, builds, credentials, backups, and Torch weights.
- [ ] Extend release checking to validate both wheel and source zip.
- [ ] Run focused tests to green.

### Task 4: Fix deterministic lint only

**Files:**
- Modify: `scripts/verify_preprocessing_equivalence.py`
- Modify: `tests/test_release_runtime.py`
- Modify: `tests/test_tool_execution.py`

- [ ] Run Ruff safe fixes only on the three named files.
- [ ] Run Ruff on `src/crc_lnm_mcp`, `scripts`, and `tests` and require PASS.

### Task 5: Verify both portability modes

**Files:**
- Verify: `tests/`
- Verify: `reports/torch_numpy_equivalence.json`

- [ ] With explicit protected reference configured, run the full pytest suite and the 101-case equivalence verifier.
- [ ] Confirm layer/logit/probability gates, zero class mismatches, demo probability, threshold, and seed.
- [ ] Clear both reference variables, extract the source archive outside the repository-parent layout, and run Ruff, pytest, release check, six independent smokes, complete-chain smoke, arbitrary-CWD smoke, and wheel-only smoke.
- [ ] Confirm only conversion-specific tests skip with the exact documented reason.

### Task 6: Rebuild and cross-platform verify

**Files:**
- Rebuild: `dist/*.whl`
- Rebuild: `dist/*.tar.gz`
- Rebuild: `crc-lnm-medical-agent-1.0.12-source.zip`
- Rewrite: `RELEASE_CHECKSUMS.sha256`

- [ ] Rebuild wheel and sdist, then generate source zip and checksums.
- [ ] Check wheel contains one NPZ and no Torch/weights; check sdist/source zip contain `.gitignore` and no protected assets.
- [ ] Run Windows and WSL Python 3.10/3.11/3.12 wheel matrices and the Linux/Windows uvx cold/warm paths.
- [ ] Record new artifact sizes and hashes.

### Task 7: Synchronize and publish branch

**Files:**
- Synchronize into: `../github_publish/crc-lnm-medical-agent/`

- [ ] Verify the existing branch is `modelscope-numpy-runtime-1.0.12` and preserve `.git`.
- [ ] Replace only managed source-tree paths from the final source zip and remove managed files absent from it.
- [ ] Run Ruff, pytest, release check, `git diff --check`, secret scan, large-file scan, model-count check, and forbidden-weight check in the Git repository.
- [ ] Stage all intended files and review the staged inventory.
- [ ] Commit with `Add NumPy single-model MCP release 1.0.12`.
- [ ] Push the existing branch to origin without force.
- [ ] If GitHub CLI authentication is valid, create the specified PR without merging it; otherwise report the compare URL.
