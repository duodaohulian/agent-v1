"""Torch-free access to the single-model deployment manifest."""

from __future__ import annotations

import json
import threading
from typing import Any

from crc_lnm_mcp.settings import MAX_METADATA_BYTES, package_asset

REQUIRED_FIELDS = {
    "architecture",
    "clinical_features",
    "ct_feature_count",
    "ct_group_counts",
    "deployment_profile",
    "ensemble_enabled",
    "feature_order_sha256",
    "independent_test_claim",
    "member_count",
    "model_schema_version",
    "package_version",
    "pathology_feature_count",
    "research_use_only",
    "runtime_asset_sha256",
    "runtime_backend",
    "selected_model_id",
    "selected_seed",
    "source_framework",
    "source_model_sha256",
    "threshold",
    "threshold_recalibrated_for_single_model",
}


class MetadataProvider:
    """Read and cache only the small deployment manifest on first use."""

    def __init__(self) -> None:
        self._manifest: dict[str, Any] | None = None
        self._lock = threading.Lock()
        self.manifest_read_count = 0

    def _load_manifest(self) -> dict[str, Any]:
        if self._manifest is not None:
            return self._manifest
        with self._lock:
            if self._manifest is not None:
                return self._manifest
            resource = package_asset("model", "deployment_manifest.json")
            with resource.open("rb") as handle:
                raw = handle.read(MAX_METADATA_BYTES + 1)
            if len(raw) > MAX_METADATA_BYTES:
                raise ValueError("deployment manifest exceeds metadata size limit")
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict) or not REQUIRED_FIELDS <= value.keys():
                raise ValueError("deployment manifest is incomplete")
            if value["member_count"] != 1 or value["ensemble_enabled"] is not False:
                raise ValueError("deployment manifest is not a real single-model profile")
            if value["research_use_only"] is not True:
                raise ValueError("deployment manifest must remain research-use-only")
            self._manifest = value
            self.manifest_read_count += 1
            return value

    def manifest(self) -> dict[str, Any]:
        return dict(self._load_manifest())

    def get_model_info(self) -> dict[str, Any]:
        manifest = self._load_manifest()
        keys = (
            "package_version",
            "deployment_profile",
            "runtime_backend",
            "source_framework",
            "source_model_sha256",
            "runtime_asset_sha256",
            "architecture",
            "model_schema_version",
            "feature_order_sha256",
            "pathology_feature_count",
            "ct_feature_count",
            "ct_group_counts",
            "clinical_features",
            "member_count",
            "ensemble_enabled",
            "original_ensemble_member_count",
            "selected_model_id",
            "selected_seed",
            "selection_method",
            "threshold",
            "threshold_source",
            "threshold_recalibrated",
            "threshold_recalibrated_for_single_model",
            "research_use_only",
            "independent_test_claim",
        )
        return {key: manifest[key] for key in keys}


__all__ = ["MetadataProvider"]
