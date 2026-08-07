"""NumPy-only predictor that preserves the archived preprocessing contract."""

from __future__ import annotations

from .numpy_model import NumpyMCAT
from .numpy_ops import softmax
from .preprocessing import NumpyPreprocessor


class SingleModelPredictor:
    def __init__(
        self,
        model: NumpyMCAT,
        preprocessor: NumpyPreprocessor,
        *,
        model_id: str,
        seed: int,
    ) -> None:
        self.model = model
        self.preprocessor = preprocessor
        self.model_id = model_id
        self.seed = seed

    def predict(
        self,
        pathology: dict[str, float],
        ct: dict[str, float],
        clinical: dict[str, int | float],
    ) -> float:
        prepared = self.preprocessor.transform(pathology, ct, clinical)
        logits, _trace = self.model.forward(prepared)
        probability = softmax(logits, axis=1)[0, 1]
        return float(probability)


__all__ = ["SingleModelPredictor"]
