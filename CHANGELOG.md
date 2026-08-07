# Changelog

## 1.0.16 �?2026-08-07

- **Tool 签名回滚�?GitHub v1.0.12 风格**：重新使�?`Literal["1.1.0"]` + `UUID4` + Pydantic BaseModel 嵌套输入 (`input: PredictMultimodalInput` / `input: CaseQCInput` / �?，这�?ModelScope STDIO 通过 FastMCP 2.14.7 验证可加载的唯一签名组合�?- **保留 v1.0.16 的中�?description 字段**�? 个工具的 `TOOL_DESCRIPTION` 字符串保持不变；`mcp.tool(name=TOOL_NAME, description=TOOL_DESCRIPTION)` �?`register()` 中继续使用�?- **测试脚本同步**：smoke 客户端改为嵌�?`input: { ... }` 调用 (例如 `input: { qc_artifact_id, source: { mode: "precomputed" } }`)�?- **`package_version` / `service_version` 升级�?1.0.16**；GitHub Actions workflow 文件名替换为 `release-matrix-1.0.16.yml`，跨平台矩阵全绿�?
## 1.0.16 �?2026-08-06

- Bumped every version reference (`pyproject.toml`, GitHub Actions workflow filename + artifact path, `scripts/check_release.py` constants, `modelscope-mcp.json`, the six tools and `runtime.py` provenance) from 1.0.14 to 1.0.16.
- Replaced `.github/workflows/release-matrix-1.0.14.yml` with `release-matrix-1.0.16.yml`; the new workflow is the only one that runs on `main` pushes.
- Updated `scripts/smoke_common.py` call arguments to match the v1.0.14+ flat parameter signatures (no nested `input`, `clinical_age` / `clinical_male` / `clinical_type` / `clinical_t` at the top level), so the cross-platform smoke gate no longer fails with Pydantic `Unexpected keyword argument`.
- README and ModelScope config updated to install `crc-lnm-medical-agent-twomeme@1.0.16`.

## 1.0.14 �?2026-08-06

- Flattened all six tool signatures: `UUID4` / `Literal` / Pydantic nested `BaseModel` parameters replaced with native `str` / `int` / `float` parameters wrapped in `Annotated[Type, Field(description=...)]`.
- Clinical inputs split into four top-level parameters (`clinical_age`, `clinical_male`, `clinical_type`, `clinical_t`) instead of a nested `clinical` object.
- Each tool now exposes a stable Chinese `description` and parameter-level `description` metadata so JSON-RPC clients (e.g. Nexent) parse the schema without `anyOf` / `pattern` complications.
- Result envelopes still carry `provenance.service_version = "1.0.14"`; cross-platform smoke gate and `check_release.py` aligned with the new parameter layout.

## 1.0.11 �?2026-08-04

- Added an isolated two-tool ModelScope STDIO deployment canary.
- Reduced direct runtime dependencies to FastMCP and Pydantic and broadened Python support to 3.10+.
- Restricted the wheel to `crc_lnm_mcp`; excluded medical models, cases, old runtime code, HTTP server code,
  Docker configuration, caches, and duplicate assets.
- Replaced duplicate/version-pinned ModelScope configurations with one minimal root configuration.
- Added real MCP client smoke testing, wheel/release checks, manual deployment instructions, and rollback guidance.
- Preserved the existing six-tool medical source for a later lazy-runtime migration; it is not enabled here.