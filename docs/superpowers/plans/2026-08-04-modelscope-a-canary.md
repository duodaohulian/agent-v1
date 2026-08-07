# ModelScope A Canary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a minimal `crc-lnm-medical-agent` STDIO canary package for ModelScope hosted deployment without shipping or invoking the existing medical runtime.

**Architecture:** Add an isolated `crc_lnm_mcp` package containing a side-effect-free FastMCP server and two metadata-only tools. Restrict setuptools discovery to that package, keep one ModelScope JSON configuration, and validate the built wheel from clean wheel-only environments with a real MCP client session.

**Tech Stack:** Python 3.10+, setuptools, FastMCP 2.x, Pydantic 2.x, pytest, MCP Python client, build, twine, uv/uvx.

---

### Task 1: Lock the release contract with failing tests

**Files:**
- Create: `tests/test_canary_import.py`
- Create: `tests/test_canary_tools.py`
- Create: `tests/test_modelscope_config.py`
- Create: `tests/test_console_entrypoint.py`
- Create: `tests/test_wheel_contents.py`
- Create: `tests/test_stdout_clean.py`
- Create: `tests/test_version_consistency.py`
- Create: `tests/test_arbitrary_cwd.py`

- [ ] Write tests for dependency-free import behavior, exact tools and payloads, one entry point, one config, README equality, dynamic package version, arbitrary CWD, clean stdout, wheel inventory, and real stdio lifecycle.
- [ ] Run the new tests against the existing code and record expected failures caused by the absent canary package and old packaging surface.

### Task 2: Implement the minimal package and packaging contract

**Files:**
- Create: `src/crc_lnm_mcp/__init__.py`
- Create: `src/crc_lnm_mcp/__main__.py`
- Create: `src/crc_lnm_mcp/server.py`
- Create: `src/crc_lnm_mcp/metadata.py`
- Modify: `pyproject.toml`
- Modify: `modelscope-mcp.json`
- Delete: `configs/modelscope-mcp.json`
- Create: `.gitignore`
- Create: `MANIFEST.in`

- [ ] Implement dynamic installed-version lookup with a safe source-tree fallback that is not another hard-coded release version.
- [ ] Register only `healthcheck` and `describe_deployment`; make `run()` enter stdio directly with no CLI parser, HTTP import, network operation, disk write, print, or eager runtime.
- [ ] Set version 1.0.11 after verifying it is unoccupied, require Python >=3.10, constrain dependencies to FastMCP/Pydantic, define one script, and discover only `crc_lnm_mcp`.
- [ ] Replace the root JSON with the exact minimal ModelScope structure and remove the duplicate formal config.
- [ ] Run the new unit/contract tests until green.

### Task 3: Add release and protocol verification tooling

**Files:**
- Create: `scripts/inspect_wheel.py`
- Create: `scripts/check_release.py`
- Create: `scripts/smoke_stdio.py`

- [ ] Implement wheel inventory/metadata inspection without extracting untrusted paths.
- [ ] Implement the twelve required release checks and fail with actionable stderr diagnostics.
- [ ] Implement a real MCP client that starts the supplied console command, initializes, sends initialized, lists tools, calls both tools, records timings/RSS, and shuts down cleanly.
- [ ] Reuse the smoke client from pytest for arbitrary-CWD and stdout/side-effect checks.

### Task 4: Rewrite operator and migration documentation

**Files:**
- Modify: `README.md`
- Create: `docs/MODELSCOPE_A_MIGRATION_AUDIT.md`
- Create: `docs/MODELSCOPE_CANARY_RELEASE.md`
- Create: `docs/MODELSCOPE_MANUAL_DEPLOYMENT.md`
- Create: `docs/LEGACY_HTTP_DEPLOYMENT.md`
- Create: `docs/ROLLBACK.md`
- Create: `CHANGELOG.md`

- [ ] Make the first README JSON block byte-for-structure identical to the root config and keep quick start canary-only.
- [ ] Document baseline/reference startup chains, dependency and wheel differences, probable failure phases, in/out scope, release procedure, ModelScope manual UI steps, evidence capture, and rollback.
- [ ] Move legacy HTTP/Docker/Nexent guidance out of quick start and clearly mark it as excluded from ModelScope plan A.

### Task 5: Build and verify clean artifacts

**Files:**
- Create: `dist/*.whl`
- Create: `dist/*.tar.gz`
- Create: `RELEASE_CHECKSUMS.sha256`
- Create: `crc-lnm-medical-agent-1.0.11-source.zip`

- [ ] Remove old build output/caches, create clean environments, and install build/test tools.
- [ ] Run `python -m build` and `python -m twine check dist/*`.
- [ ] Inspect the wheel and run `scripts/check_release.py`.
- [ ] Install only the wheel in unrelated temporary directories and run pytest plus the real stdio smoke flow.
- [ ] Test all locally available Python 3.10/3.11/3.12 runtimes without claiming unavailable versions.
- [ ] Install/use uv and verify `uvx` against the local wheel without contacting the unpublished package name on PyPI.
- [ ] Measure import, initialize, tools/list, and peak RSS; compare honestly to targets.
- [ ] Produce checksums and a cache-free source archive, then rerun final checks.
