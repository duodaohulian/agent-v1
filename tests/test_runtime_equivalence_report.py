from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_torch_numpy_equivalence_report_meets_release_thresholds() -> None:
    report_path = ROOT / "reports/torch_numpy_equivalence.json"
    layerwise_path = ROOT / "reports/torch_numpy_layerwise.csv"
    assert report_path.is_file()
    assert layerwise_path.is_file()
    report = json.loads(report_path.read_text("utf-8"))
    assert report["status"] == "PASS"
    assert report["case_count"] >= 101
    assert report["synthetic_case_count"] >= 100
    assert report["preprocessing_max_absolute_error"] <= 1e-7
    assert report["layerwise_max_absolute_error"] <= 1e-5
    assert report["logit_max_absolute_error"] <= 1e-5
    assert report["probability_max_absolute_error"] <= 1e-6
    assert report["predicted_class_mismatches"] == 0
    assert abs(report["demo"]["torch_probability"] - 0.5726384520530701) <= 1e-7
    assert abs(report["demo"]["numpy_probability"] - 0.5726384520530701) <= 1e-6
    with layerwise_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows
    assert any(row["layer"] == "classifier.logits" for row in rows)
    assert max(float(row["max_absolute_error"]) for row in rows) <= 1e-5
