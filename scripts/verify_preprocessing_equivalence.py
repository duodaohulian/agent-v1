from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crc_lnm_mcp.inference.preprocessing import NumpyPreprocessor  # noqa: E402
from wei_multimodal.artifacts.bundle import schema_from_dict  # noqa: E402
from wei_multimodal.data.preprocessing import FoldPreprocessor  # noqa: E402


def read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    bundle = ROOT / "models" / "deployment_bundle"
    demo = ROOT / "demo" / "cases" / "demo_case_001"
    schema_payload = read(bundle / "schema.json")
    schema = schema_from_dict(schema_payload)
    pathology = read(demo / "pathology_features.json")
    ct = read(demo / "ct_features.json")
    clinical = read(demo / "clinical.json")
    row = {
        **{f"pathology::{key}": value for key, value in pathology.items()},
        **{f"ct::{key}": value for key, value in ct.items()},
        **clinical,
    }
    columns = [
        *schema.pathology_output_columns,
        *schema.ct_output_columns,
        "age",
        "male",
        "Type",
        "T",
    ]
    legacy = FoldPreprocessor.load(bundle, schema).transform(pd.DataFrame([row], columns=columns))
    current = NumpyPreprocessor.from_files(
        schema_payload,
        bundle / "preprocessing.json",
        bundle / "preprocessing.npz",
    ).transform(pathology, ct, clinical)
    names = (
        "pathology",
        "ct_shape",
        "ct_original",
        "ct_wavelet",
        "ct_transformed",
        "age",
        "male",
        "type_index",
        "t_stage_index",
    )
    deltas = {
        name: float(np.max(np.abs(getattr(legacy, name) - getattr(current, name))))
        for name in names
    }
    all_names = [
        *schema.pathology_output_columns,
        *schema.ct_output_columns,
        *schema.clinical_columns,
    ]
    report = {
        "passed": max(deltas.values()) <= 1e-7,
        "maximum_absolute_delta": max(deltas.values()),
        "group_maximum_absolute_delta": deltas,
        "feature_order_sha256": hashlib.sha256("\n".join(all_names).encode("utf-8")).hexdigest(),
        "reference": "archived FoldPreprocessor pandas path",
        "candidate": "1.0.12 NumPy-only inference path",
        "case_ref": "demo_case_001",
    }
    output = ROOT / "reports" / "preprocessing_equivalence.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
