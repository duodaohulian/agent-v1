# Local Release Environment Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local release acceptance independent of the active Conda base by creating and exclusively using a project-local Python 3.10â€?.12 release environment.

**Architecture:** `setup_release_env.ps1` discovers installed interpreters, rejects unsupported versions, selects 3.12 then 3.11 then 3.10, and owns `.venv-release` creation and dependency installation. `release_verify.ps1` resolves the repository root from `$PSScriptRoot`, fail-fast validates `.venv-release\Scripts\python.exe`, and routes every non-wheel-only Python call through that exact path while retaining a separate temporary wheel-only environment.

**Tech Stack:** Windows PowerShell, CPython `venv`/`pip`, Pytest, Build, Twine, Ruff, Mypy.

---

### Task 1: Preserve baseline evidence and define regression contracts

**Files:**
- Create: `docs/RELEASE_ENVIRONMENT_BASELINE.md`
- Modify: `tests/test_release_closure.py`

- [ ] **Step 1: Save the exact `py -0p`, `where.exe python`, `python --version`, and `conda info --envs` results**

Record that `py` is unavailable, bare Python is `<TEMP_WORKSPACE>\Anaconda\python.exe` 3.13.5, and list every Conda environment observed. Also record direct probes proving available 3.12.13, 3.11.15, and 3.10.20 interpreters.

- [ ] **Step 2: Add failing static contract tests**

Add tests that require:

```python
assert '$ReleasePython = Join-Path $ProjectRoot ".venv-release\\Scripts\\python.exe"' in verifier
assert '[string]$Python = "python"' not in verifier
assert "Release virtual environment not found. Run scripts/setup_release_env.ps1 first." in verifier
assert "RELEASE ENVIRONMENT SETUP: PASS" in setup
assert '.venv-release/' in gitignore
```

Also assert the setup script contains selection order `3.12`, `3.11`, `3.10`, import verification for `build, twine, pytest, psutil`, and no upload/Git/ModelScope mutation commands.

- [ ] **Step 3: Run the focused test and observe RED**

Run the known Python 3.12 interpreter with:

```powershell
& '<TEMP_WORKSPACE>\python.exe' -m pytest tests/test_release_closure.py -q
```

Expected: failures because `setup_release_env.ps1` and the explicit `$ReleasePython` verifier contract do not yet exist.

### Task 2: Implement isolated release-environment setup

**Files:**
- Create: `scripts/setup_release_env.ps1`
- Modify: `.gitignore`

- [ ] **Step 1: Implement fail-fast command execution and interpreter probing**

Use `$PSScriptRoot` to resolve `$ProjectRoot`. Probe `py -0p` when available, then local machine candidates without modifying them. For every candidate, execute a small `sys.version_info` probe, reject 3.13 and every unsupported major/minor, exclude the active Conda base interpreter, deduplicate absolute paths, and select the highest-priority supported minor.

- [ ] **Step 2: Safely create or rebuild `.venv-release`**

If an existing environment has a different interpreter minor from the selected 3.12/3.11/3.10 candidate, resolve its absolute path, verify it remains under `$ProjectRoot`, remove it, and run:

```powershell
& $SelectedPython -m venv $ReleaseVenv
```

Then confirm the resulting interpreter reports one of `(3,10)`, `(3,11)`, `(3,12)`.

- [ ] **Step 3: Install only through the release interpreter**

Run:

```powershell
& $ReleasePython -m pip install --upgrade pip setuptools wheel
& $ReleasePython -m pip install build twine pytest psutil ruff mypy
& $ReleasePython -m pip install -e $ProjectRoot
& $ReleasePython -c "import build, twine, pytest, psutil; print('verification dependencies: ok')"
```

Every nonzero exit must throw. Print the selected executable and version, and print `RELEASE ENVIRONMENT SETUP: PASS` only after the import check.

- [ ] **Step 4: Add the explicit ignore entry**

Add `.venv-release/` to `.gitignore` even though the broader `.venv*/` pattern already matches it, because the acceptance specification requires the named entry.

- [ ] **Step 5: Run focused tests and observe setup contracts GREEN**

Run the focused closure tests; setup-related assertions must pass.

### Task 3: Make release verification interpreter-explicit

**Files:**
- Modify: `scripts/release_verify.ps1`

- [ ] **Step 1: Remove the bare-Python parameter and resolve the local interpreter**

Define exactly:

```powershell
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$ReleasePython = Join-Path $ProjectRoot ".venv-release\Scripts\python.exe"
```

If the file is absent, throw exactly `Release virtual environment not found. Run scripts/setup_release_env.ps1 first.` before deleting or rebuilding artifacts.

- [ ] **Step 2: Add a strict version gate with evidence**

Query the absolute interpreter for a machine-readable major/minor and human version. Permit only 3.10, 3.11, and 3.12. On rejection, include both `$ReleasePython` and the actual version in the error.

- [ ] **Step 3: Route all release Python operations through `$ReleasePython`**

Change `Invoke-Python` to execute `& $ReleasePython @Arguments`. Keep build, Twine, source Pytest, release checks, wheel inspection, source-zip support, and checksum-related Python operations on this interpreter. Preserve `$VenvPython` only inside the separately created temporary wheel-only environment.

- [ ] **Step 4: Preserve the PASS gate**

Keep `LOCAL RELEASE VERIFICATION: PASS` as the final statement inside the successful `try` path, after checksum generation; do not print it on any failure path.

- [ ] **Step 5: Run focused closure tests and observe GREEN**

Run `tests/test_release_closure.py`; all assertions must pass.

### Task 4: Create and verify the real release environment

**Files:**
- Generated/ignored: `.venv-release/`

- [ ] **Step 1: Execute environment setup from the repository root**

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\setup_release_env.ps1"
```

Expected final line: `RELEASE ENVIRONMENT SETUP: PASS`.

- [ ] **Step 2: Record interpreter and dependency versions**

Use only `.venv-release\Scripts\python.exe` to report Python, Build, Twine, Pytest, Psutil, Ruff, and Mypy versions. Re-run the required import check and require `verification dependencies: ok`.

### Task 5: Complete release acceptance and artifact audit

**Files:**
- Regenerated: `dist/crc_lnm_medical_agent-1.0.11-py3-none-any.whl`
- Regenerated: `dist/crc_lnm_medical_agent-1.0.11.tar.gz`
- Regenerated: `crc-lnm-medical-agent-1.0.11-source.zip`
- Regenerated: `RELEASE_CHECKSUMS.sha256`

- [ ] **Step 1: Run the complete verifier**

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\release_verify.ps1"
```

Expected final line: `LOCAL RELEASE VERIFICATION: PASS`.

- [ ] **Step 2: Capture acceptance evidence**

Record the source and wheel-only Pytest totals, smoke result and exact tools, artifact file names/sizes, and whether artifacts were rebuilt.

- [ ] **Step 3: Independently audit artifact metadata and checksums**

Run `scripts/inspect_wheel.py` with the release interpreter, confirm the wheel contains only `crc_lnm_mcp` plus distribution metadata, confirm version 1.0.11 and exact dependencies `fastmcp==2.14.7` and `pydantic==2.13.4`, and compare each newly computed SHA-256 with `RELEASE_CHECKSUMS.sha256`.

- [ ] **Step 4: Run final regression gates**

Run the full source test suite, Ruff, and Mypy from `.venv-release`. No upload, Git, or ModelScope command is part of acceptance.
