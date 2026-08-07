from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION_JSON = ROOT / "reports" / "single_model_selection.json"
COMPARISON_CSV = ROOT / "reports" / "single_model_comparison.csv"
REGRESSION_JSON = ROOT / "reports" / "single_model_regression.json"
EXPECTED_SEEDS = [2024, 3407, 5280, 7319, 9021]


def _load_json(path: Path) -> dict[str, object]:
    assert path.is_file(), f"required report is missing: {path.relative_to(ROOT)}"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_selection_uses_all_five_members_and_demo_only() -> None:
    report = _load_json(SELECTION_JSON)
    candidates = report["candidates"]
    assert isinstance(candidates, list)
    assert [row["seed"] for row in candidates] == EXPECTED_SEEDS
    assert report["selection_dataset"] == "demo_case_001"
    assert report["selection_dataset_case_count"] == 1
    assert report["selection_method"] == "minimum_mae_to_ensemble"
    assert report["test_labels_used"] is False
    assert report["release_case_jsonl_used"] is False


def test_selected_model_is_deterministic() -> None:
    report = _load_json(SELECTION_JSON)
    candidates = report["candidates"]
    assert isinstance(candidates, list)
    selected = [row for row in candidates if row["selected"]]
    assert len(selected) == 1
    minimum_mae = min(row["mae_to_ensemble"] for row in candidates)
    assert selected[0]["mae_to_ensemble"] == minimum_mae
    assert report["selected_model_id"] == selected[0]["model_id"]
    assert report["selected_seed"] == selected[0]["seed"]
    assert report["limitations"]


def test_comparison_csv_matches_selection_report() -> None:
    report = _load_json(SELECTION_JSON)
    assert COMPARISON_CSV.is_file()
    with COMPARISON_CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 5
    assert [int(row["seed"]) for row in rows] == EXPECTED_SEEDS
    assert sum(row["selected"].lower() == "true" for row in rows) == 1
    assert {row["model_id"] for row in rows} == {row["model_id"] for row in report["candidates"]}


def test_regression_records_single_and_ensemble_outputs() -> None:
    report = _load_json(REGRESSION_JSON)
    assert report["case_ref"] == "demo_case_001"
    assert 0.0 <= report["ensemble_probability"] <= 1.0
    assert 0.0 <= report["single_model_probability"] <= 1.0
    assert report["absolute_delta"] == abs(
        report["single_model_probability"] - report["ensemble_probability"]
    )
    assert report["member_count"] == 1
    assert report["ensemble_enabled"] is False
    assert report["threshold_unchanged"] is True
    assert report["preprocessing_checksum"]
    assert report["feature_ordering_checksum"]
