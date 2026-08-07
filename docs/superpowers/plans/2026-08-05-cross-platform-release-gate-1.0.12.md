# CRC-LNM MCP 1.0.12 Cross-Platform Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and execute a wheel-only Python 3.10/3.11/3.12 and Windows/Linux release gate without changing model or six-tool behavior.

**Architecture:** Keep the published wheel as the only server-code input under test. Extend the existing MCP client smoke harness to accept console arguments, add platform launch/audit wrappers around it, and make GitHub Actions consume the built wheel artifact across a six-cell OS/Python matrix. Record only observed local/CI evidence and classify unexecuted ModelScope checks explicitly.

**Tech Stack:** Python 3.10�?.12, FastMCP/MCP STDIO, uv/uvx, PowerShell, Bash, GitHub Actions, pytest, psutil, PyTorch CPU.

---

### Task 1: Preserve the pre-gate release

**Files:**
- Verify: `dist/crc_lnm_medical_agent-1.0.12-py3-none-any.whl`
- Verify: `dist/crc_lnm_medical_agent-1.0.12.tar.gz`
- Verify: `crc-lnm-medical-agent-1.0.12-source.zip`
- Verify: `RELEASE_CHECKSUMS.sha256`
- Create externally: `../release_1.0.12_before_cross_platform_gate/`

- [x] **Step 1:** Record the four current artifacts and wheel SHA-256.
- [x] **Step 2:** Copy the complete workspace without overwriting an existing backup.
- [x] **Step 3:** Verify copied file count/bytes and wheel SHA-256.

### Task 2: Specify the cross-platform gate with failing tests

**Files:**
- Create: `tests/test_cross_platform_release_gate.py`
- Test: `tests/test_cross_platform_release_gate.py`

- [ ] **Step 1:** Assert the workflow exists with `ubuntu-latest`/`windows-latest`, Python `3.10`/`3.11`/`3.12`, wheel artifact download, six independent smokes, full smoke, no editable install, no secrets, and artifact upload.
- [ ] **Step 2:** Assert Linux and published-style scripts exist, use the final wheel, exercise prediction twice, and emit the exact PASS markers only after all commands succeed.
- [ ] **Step 3:** Assert the risk report and matrix result schema expose Python/OS, timing, RSS, weight count, selected seed, member count, ensemble flag, and Torch lazy-load evidence.
- [ ] **Step 4:** Run `python -m pytest tests/test_cross_platform_release_gate.py -q` and confirm failure because the new workflow/scripts/docs do not yet exist.

### Task 3: Implement reusable published-style wheel smoke

**Files:**
- Modify: `scripts/smoke_common.py`
- Create: `scripts/smoke_published_style_local_wheel.py`
- Test: `tests/test_cross_platform_release_gate.py`

- [ ] **Step 1:** Add optional server arguments to `run_smoke()` and the CLI while retaining existing callers.
- [ ] **Step 2:** Implement a wrapper that verifies the installed package is outside the source tree, runs all six independent smokes plus the full chain against a supplied command/arguments, verifies prediction reuse and invariants, and writes an aggregate JSON.
- [ ] **Step 3:** Run the focused tests and existing STDIO tests; confirm all pass.

### Task 4: Add Windows/Linux verification and Linux uvx audit

**Files:**
- Modify: `scripts/release_verify_full.ps1`
- Create: `scripts/release_verify_full_linux.sh`
- Create: `scripts/audit_linux_uvx_cold_start.sh`
- Test: `tests/test_cross_platform_release_gate.py`

- [ ] **Step 1:** Make the Windows verifier install the non-editable final wheel, run wheel tests and all smokes, and print `WINDOWS FULL RELEASE VERIFICATION: PASS` only at the end.
- [ ] **Step 2:** Implement the Linux verifier with a fresh venv, dependency check, installed-origin check from a temporary CWD, wheel inspection, six independent smokes, full chain, and `LINUX FULL RELEASE VERIFICATION: PASS` only at the end.
- [ ] **Step 3:** Implement the uv audit with separate resolve/download/install, cold MCP, warm MCP, first/second prediction, RSS, wheel/dependency-size fields, and machine-readable JSON output.
- [ ] **Step 4:** Run focused tests and shell syntax checks.

### Task 5: Add the GitHub Actions six-cell matrix

**Files:**
- Create: `.github/workflows/release-matrix-1.0.12.yml`
- Test: `tests/test_cross_platform_release_gate.py`

- [ ] **Step 1:** Build the 1.0.12 wheel once and upload it as an artifact.
- [ ] **Step 2:** Download and install that wheel in fresh `ubuntu-latest`/`windows-latest` jobs for Python 3.10/3.11/3.12 without editable installation.
- [ ] **Step 3:** Run installed-origin, exact tool, lazy Torch, checksum, one-weight, six-smoke, full-chain, and prediction reuse gates.
- [ ] **Step 4:** Upload per-cell JSON/log artifacts and run the focused workflow contract test.

### Task 6: Execute local Windows and Linux matrices

**Files:**
- Create: `reports/cross_platform_gate/windows-py310.json`
- Create: `reports/cross_platform_gate/windows-py311.json`
- Create: `reports/cross_platform_gate/windows-py312.json`
- Create: `reports/cross_platform_gate/linux-py310.json`
- Create: `reports/cross_platform_gate/linux-py311.json`
- Create: `reports/cross_platform_gate/linux-py312.json`
- Create: `reports/linux_uvx_cold_start.json`

- [ ] **Step 1:** Discover or install isolated Python 3.10/3.11/3.12 runtimes.
- [ ] **Step 2:** Install the final wheel non-editably with dependencies in every environment and run the full gate; do not skip prediction.
- [ ] **Step 3:** Run the Linux uvx cold/warm audit with a fresh uv cache and record stage-separated timings and sizes.
- [ ] **Step 4:** If a cell fails, classify the dependency/runtime cause, write a failing report, and apply only a test-proven compatibility fix before rerunning all cells.

### Task 7: Document risk and regenerate artifacts if sources change

**Files:**
- Create: `docs/MODELSCOPE_RUNTIME_RISK_1.0.12.md`
- Create: `docs/CROSS_PLATFORM_RELEASE_GATE_1.0.12.md`
- Modify: `scripts/build_release_artifacts.py`
- Rebuild: `dist/crc_lnm_medical_agent-1.0.12-py3-none-any.whl`
- Rebuild: `dist/crc_lnm_medical_agent-1.0.12.tar.gz`
- Rebuild: `crc-lnm-medical-agent-1.0.12-source.zip`
- Rebuild: `RELEASE_CHECKSUMS.sha256`

- [ ] **Step 1:** Summarize A–S using only observed results, including all unverified items and a low/medium/high ModelScope risk rating without invented timeout thresholds.
- [ ] **Step 2:** If any packaged source changed, rebuild all four artifacts and replace the pre-gate checksum with new hashes.
- [ ] **Step 3:** Reinstall the final rebuilt wheel and rerun the complete local gate.
- [ ] **Step 4:** Run pytest, Ruff, twine, release checks, checksum verification, report-schema checks, and residual-process checks before recommending or withholding release.

### Self-review

- Requirements covered: backup, three Python versions, Windows/Linux, actual Linux inference, uvx cold/warm separation, CI matrix, one process/six tools, exact invariants, release scripts, risk report, artifact regeneration, and A–S output.
- Scope protection: no model, threshold, preprocessing, feature, clinical-field, tool-name, or medical semantic changes are planned.
- No placeholders or unbounded production features are included; GitHub-hosted execution is represented by workflow creation, while local Docker/WSL execution supplies current Linux evidence.
