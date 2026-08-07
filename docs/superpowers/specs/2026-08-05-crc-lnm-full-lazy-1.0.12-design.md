# CRC-LNM Full Lazy 1.0.12 Design

## Purpose

Build package version 1.0.12 on the verified 1.0.11 ModelScope STDIO canary shell. The
release restores exactly six medical tools in one package, one console script, and one MCP
process while replacing the five-member ensemble with one evidence-selected model. It does
not upload artifacts, modify 1.0.11, retrain a model, recalibrate a threshold, use HTTP, or
operate PyPI, GitHub, or ModelScope.

## Protected Baseline

The workspace is not a Git repository, so the requested branch cannot be created. Before
this specification was written, the complete current tree was copied to the sibling directory
`release_1.0.10_backup_before_full_lazy_1.0.12_20260805`. Source and backup contain 9,413
files totaling 260,430,615 bytes with identical relative paths and lengths. SHA-256 also
matches for the package metadata, ModelScope configuration, 1.0.11 source archive, wheel,
sdist, deployment manifest, and all five model weights. The older pre-canary backup and the
1.0.11 source archive remain unchanged.

## Chosen Approach

The 1.0.12 runtime will be self-contained under `src/crc_lnm_mcp`. The old
`src/wei_multimodal` implementation and all five original weights remain in the development
archive but are excluded from the 1.0.12 wheel. Required contracts and business rules will be
ported surgically instead of importing the legacy package at runtime. This keeps the release
surface explicit and prevents legacy eager-loading, HTTP, pandas, training, and five-model
dependencies from leaking into startup.

Rejected alternatives are:

- Lazy-importing `wei_multimodal`, which retains its coupled dependency graph and makes wheel
  contents and import boundaries difficult to prove.
- Converting `wei_multimodal` itself into the deployment package, which risks altering the
  archived 1.0.10 implementation and reintroducing the old startup lifecycle.

## Package Architecture

`server.py` creates FastMCP lazily, constructs only a lightweight `RuntimeProvider`, registers
the six tool modules, and runs `transport="stdio"`. It contains no top-level Torch, NumPy,
pandas, sklearn, model class, weight, case corpus, or prediction-service import.

The package is divided into:

- `contracts/`: Pydantic request, response, status, warning, error, provenance, and artifact
  contracts. Existing 1.0.10 field names and contract version 1.1.0 are retained unless a
  schema comparison proves a required additive field cannot be optional.
- `tools/`: six independent FastMCP adapters, one per formal tool name. Registration creates
  schemas only and performs no business operation.
- `services/`: metadata, case QC, CT preparation, pathology preparation, prediction, and report
  business logic. Services do not depend on FastMCP context objects.
- `inference/`: delayed Torch import, checksum verification, model construction, NumPy
  preprocessing, and single-model prediction.
- `assets/`: lightweight metadata, schema, preprocessing parameters, one model configuration,
  exactly one model state, one case JSONL resource, and the report template if Jinja2 remains
  justified.

## Runtime Providers

`RuntimeProvider` owns three independently lazy layers:

1. `MetadataProvider` reads bounded lightweight JSON metadata and never imports Torch. It
   serves model information and exposes selected-model metadata to the other providers.
2. `CaseAndFeatureProvider` opens the packaged JSONL only on the first case-related call,
   builds an in-memory `case_ref -> byte offset` index, validates allowlisted case references,
   and retrieves one bounded record at a time. It owns the in-process artifact store used by
   QC, feature preparation, and reporting and never loads weights.
3. `PredictionProvider` is constructed as a lightweight holder. Its first prediction acquires
   a lock, delays importing Torch and model modules, validates model and preprocessing
   checksums, creates one predictor, and caches it. Concurrent callers reuse the same
   initialization result. A failed initialization is converted into a structured error and
   may have at most one controlled retry; it never terminates the MCP process or loops.

Provider diagnostics record model `load_count`, `load_seconds`, RSS delta, and prediction
count without returning absolute paths.

## Tool and Data Flow

The formal tool set is exactly:

1. `crc_lnm_get_model_info`
2. `crc_lnm_case_data_qc`
3. `crc_lnm_prepare_ct_features`
4. `crc_lnm_prepare_pathology_features`
5. `crc_lnm_predict_multimodal`
6. `crc_lnm_generate_report`

The complete workflow is initialize, tools/list, model info, QC, CT preparation, pathology
preparation, prediction, report, and graceful shutdown. Artifact identifiers bind every stage
to the same case and trace. The report consumes an existing prediction artifact and cannot
reach the prediction provider.

Only prediction may import Torch or read model bytes. Model information reads only metadata.
QC and feature tools read a single indexed case and create bounded in-memory artifacts.
Reporting reads existing artifacts. No stage accepts a filesystem path, downloads content,
spawns workers, writes into the installed package, or performs startup warmup.

## Single-Model Selection

All five candidates use the same `attention_path_ct_clinical` architecture, input dimensions,
preprocessing bundle, and approximately 3.08 MB state size. Seeds are 2024, 3407, 5280,
7319, and 9021. The repository contains an overall development OOF ROC-AUC reference of
0.7749 but no comparable per-seed validation metrics, so it cannot support priority-1 model
selection.

Selection therefore uses only the approved non-private `demo_case_001`. The original ensemble
and every single member are measured on identical prepared inputs. The model minimizing
absolute probability error to the ensemble is selected. Ties are resolved by model size, load
time, inference time, then lexical seed/model id as specified. The release JSONL is excluded
from selection because it is not proven to be a non-test, non-private selection set.

Because there is only one demo case, reports label this result a deployment-proximity choice,
not a performance-optimal model. The original ensemble threshold is retained with an explicit
uncalibrated-single-model warning because no saved per-model threshold has been found.
`research_use_only` stays true and `independent_test_claim` stays false.

One deployment manifest is the sole source of selected model id, seed, checksums, threshold
source, `member_count=1`, `ensemble_enabled=false`, package version, and selection method.
Python modules do not hard-code the selected directory name.

## Preprocessing and Dependencies

Runtime preprocessing uses NumPy parameters exported from the existing preprocessing bundle.
Its feature order, category mapping, constant-column behavior, scaling, and output values are
compared numerically with the legacy pandas/scikit-learn path before those dependencies are
removed. The required feature counts remain pathology 768 and CT 1,409 split into 14 shape,
93 original, 744 wavelet, and 558 transformed features, plus the four locked clinical fields.

Expected runtime dependencies are FastMCP 2.14.7, Pydantic 2.13.4, NumPy, and CPU Torch.
Pandas, scikit-learn, imbalanced-learn, PyYAML, Starlette, and Uvicorn are excluded unless a
runtime import audit proves an unavoidable direct use; HTTP dependencies are not accepted as
direct project dependencies. Jinja2 remains only if the verified report contract requires the
existing template and a standard-library equivalent would change output.

## Errors and Safety

Known validation and stage-order failures retain stable structured error codes. Unexpected
exceptions are logged only to stderr and converted to tool-specific public errors without
stack traces, paths, secrets, or patient data. stdout is reserved for MCP protocol frames.

Case references match a strict allowlist pattern and must exist in the packaged index. JSONL
records, JSON metadata, model states, preprocessing assets, and artifacts have explicit size
and dimension bounds. Manifest SHA-256 values are verified before use. Artifact storage is
bounded and process-local; any optional cache uses an atomic write in a user temporary
directory and cache failure is nonfatal.

## Test and Delivery Strategy

Implementation follows the mandated Stage A through H order using red-green-refactor cycles.
Each stage first adds a failing focused test, confirms the expected failure, adds the minimal
implementation, and runs the focused and cumulative suites before proceeding.

Tests prove exact tool enumeration, Torch exclusion from import/initialize/list and five
lightweight operations, lazy single-model loading, checksum enforcement, one concurrent model
instance, second-call reuse, structured load failure, feature ordering and dimensions, path
rejection, arbitrary CWD, read-only installation, no downloads, no HTTP configuration, clean
stdout, one weight in the wheel, six independent smokes, and the complete STDIO pipeline.

The clean Python 3.12 release workflow builds wheel and sdist, runs Twine and release
inspection, installs only the wheel, runs from an arbitrary CWD, and records real timing,
memory, process, network, and stdout evidence. Python 3.10 and 3.11 are tested when the
already-available local interpreters can install the pinned CPU runtime; unsupported or failed
combinations are reported rather than inferred.

Final deliverables include every document, JSON/CSV report, smoke script, release verifier,
wheel, sdist, source zip, and checksum file listed in the approved request. No release or
external deployment operation is part of this work.
