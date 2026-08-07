"""NumPy-only inference preprocessing equivalent to the archived pandas path."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

Float32Array = NDArray[np.float32]
Int64Array = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class PreparedArrays:
    pathology: Float32Array
    ct_shape: Float32Array
    ct_original: Float32Array
    ct_wavelet: Float32Array
    ct_transformed: Float32Array
    age: Float32Array
    male: Float32Array
    type_index: Int64Array
    t_stage_index: Int64Array


class NumpyPreprocessor:
    """Apply saved means, scales, and category maps without pandas/sklearn."""

    def __init__(
        self,
        *,
        group_columns: dict[str, tuple[str, ...]],
        means: dict[str, NDArray[np.float64]],
        scales: dict[str, NDArray[np.float64]],
        category_maps: dict[str, dict[str, int]],
    ) -> None:
        self.group_columns = group_columns
        self.means = means
        self.scales = scales
        self.category_maps = category_maps

    @classmethod
    def from_files(
        cls,
        schema: dict[str, Any],
        metadata_path: Path,
        arrays_path: Path,
    ) -> NumpyPreprocessor:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("schema_version") != schema.get("version"):
            raise ValueError("preprocessing schema version mismatch")
        group_columns = {
            group: tuple(str(name) for name in names)
            for group, names in metadata.get("group_columns", {}).items()
        }
        expected = {
            "pathology": tuple(f"pathology::{name}" for name in schema["pathology_features"]),
            "ct_shape": tuple(f"ct::{name}" for name in schema["ct_shape"]),
            "ct_original": tuple(f"ct::{name}" for name in schema["ct_original"]),
            "ct_wavelet": tuple(f"ct::{name}" for name in schema["ct_wavelet"]),
            "ct_transformed": tuple(f"ct::{name}" for name in schema["ct_transformed"]),
            "age": ("age",),
        }
        if group_columns != expected:
            raise ValueError("preprocessing feature order mismatch")
        means: dict[str, NDArray[np.float64]] = {}
        scales: dict[str, NDArray[np.float64]] = {}
        with np.load(arrays_path, allow_pickle=False) as arrays:
            for group, columns in expected.items():
                mean = np.asarray(arrays[f"mean__{group}"], dtype=np.float64).copy()
                scale = np.asarray(arrays[f"scale__{group}"], dtype=np.float64).copy()
                if mean.shape != (len(columns),) or scale.shape != (len(columns),):
                    raise ValueError("preprocessing array dimension mismatch")
                if not np.isfinite(mean).all() or not np.isfinite(scale).all():
                    raise ValueError("preprocessing arrays contain non-finite values")
                if np.any(scale == 0):
                    raise ValueError("preprocessing scale contains zero")
                means[group] = mean
                scales[group] = scale
        return cls(
            group_columns=expected,
            means=means,
            scales=scales,
            category_maps={
                field: {str(key): int(value) for key, value in mapping.items()}
                for field, mapping in metadata["category_maps"].items()
            },
        )

    @staticmethod
    def _category_key(value: int | float) -> str:
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("clinical category is non-finite")
        return str(int(numeric)) if numeric.is_integer() else format(numeric, ".15g")

    def transform(
        self,
        pathology: dict[str, float],
        ct: dict[str, float],
        clinical: dict[str, int | float],
    ) -> PreparedArrays:
        combined: dict[str, int | float] = {
            **{f"pathology::{key}": value for key, value in pathology.items()},
            **{f"ct::{key}": value for key, value in ct.items()},
            **clinical,
        }
        transformed: dict[str, Float32Array] = {}
        for group, columns in self.group_columns.items():
            try:
                values = np.asarray([[combined[name] for name in columns]], dtype=np.float64)
            except KeyError as exc:
                raise ValueError(f"missing preprocessing feature: {exc.args[0]}") from exc
            if not np.isfinite(values).all():
                raise ValueError(f"{group} contains non-finite values")
            standardized = (values - self.means[group]) / self.scales[group]
            transformed[group] = standardized.astype(np.float32, copy=False)
        male = float(clinical["male"])
        if male not in {0.0, 1.0}:
            raise ValueError("clinical.male must be 0 or 1")
        type_key = self._category_key(clinical["Type"])
        t_key = self._category_key(clinical["T"])
        if type_key not in self.category_maps["Type"]:
            raise ValueError("clinical.Type is outside the trained vocabulary")
        if t_key not in self.category_maps["T"]:
            raise ValueError("clinical.T is outside the trained vocabulary")
        return PreparedArrays(
            pathology=transformed["pathology"],
            ct_shape=transformed["ct_shape"],
            ct_original=transformed["ct_original"],
            ct_wavelet=transformed["ct_wavelet"],
            ct_transformed=transformed["ct_transformed"],
            age=transformed["age"],
            male=np.asarray([[male]], dtype=np.float32),
            type_index=np.asarray([self.category_maps["Type"][type_key]], dtype=np.int64),
            t_stage_index=np.asarray([self.category_maps["T"][t_key]], dtype=np.int64),
        )


__all__ = ["NumpyPreprocessor", "PreparedArrays"]
