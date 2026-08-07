"""Fixed NumPy implementation of the verified seed_2024 MCAT graph."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from numpy.typing import NDArray

from .numpy_ops import gelu_exact, layer_norm, linear, multihead_attention
from .preprocessing import PreparedArrays

Float32Array = NDArray[np.float32]


class NumpyMCAT:
    def __init__(self, parameters: Mapping[str, Float32Array]) -> None:
        self.parameters = parameters

    def _parameter(self, source_key: str) -> Float32Array:
        return self.parameters[source_key.replace(".", "__")]

    @staticmethod
    def _record(trace: dict[str, Float32Array], name: str, value: Float32Array) -> None:
        trace[name] = np.asarray(value, dtype=np.float32).copy()

    def _feature_encoder(
        self,
        values: Float32Array,
        prefix: str,
        trace: dict[str, Float32Array],
    ) -> Float32Array:
        first = linear(
            values,
            self._parameter(f"{prefix}.network.0.weight"),
            self._parameter(f"{prefix}.network.0.bias"),
        )
        self._record(trace, f"{prefix}.linear_1", first)
        first = gelu_exact(first)
        self._record(trace, f"{prefix}.gelu_1", first)
        first = layer_norm(
            first,
            self._parameter(f"{prefix}.network.2.weight"),
            self._parameter(f"{prefix}.network.2.bias"),
            eps=1e-5,
        )
        self._record(trace, f"{prefix}.layer_norm_1", first)
        second = linear(
            first,
            self._parameter(f"{prefix}.network.4.weight"),
            self._parameter(f"{prefix}.network.4.bias"),
        )
        self._record(trace, f"{prefix}.linear_2", second)
        second = gelu_exact(second)
        self._record(trace, f"{prefix}.gelu_2", second)
        second = layer_norm(
            second,
            self._parameter(f"{prefix}.network.6.weight"),
            self._parameter(f"{prefix}.network.6.bias"),
            eps=1e-5,
        )
        self._record(trace, f"{prefix}.layer_norm_2", second)
        return second

    def _clinical_encoder(
        self,
        batch: PreparedArrays,
        trace: dict[str, Float32Array],
    ) -> Float32Array:
        continuous = np.concatenate([batch.age, batch.male], axis=1).astype(np.float32)
        continuous = linear(
            continuous,
            self._parameter("clinical_encoder.continuous_encoder.0.weight"),
            self._parameter("clinical_encoder.continuous_encoder.0.bias"),
        )
        self._record(trace, "clinical_encoder.continuous_linear", continuous)
        continuous = gelu_exact(continuous)
        self._record(trace, "clinical_encoder.continuous_gelu", continuous)
        continuous = layer_norm(
            continuous,
            self._parameter("clinical_encoder.continuous_encoder.2.weight"),
            self._parameter("clinical_encoder.continuous_encoder.2.bias"),
            eps=1e-5,
        )
        self._record(trace, "clinical_encoder.continuous_layer_norm", continuous)
        type_embedding = self._parameter("clinical_encoder.type_embedding.weight")[
            batch.type_index
        ]
        t_embedding = self._parameter("clinical_encoder.t_stage_embedding.weight")[
            batch.t_stage_index
        ]
        projected = np.concatenate([continuous, type_embedding, t_embedding], axis=1).astype(
            np.float32
        )
        projected = linear(
            projected,
            self._parameter("clinical_encoder.projection.0.weight"),
            self._parameter("clinical_encoder.projection.0.bias"),
        )
        self._record(trace, "clinical_encoder.projection_linear_1", projected)
        projected = gelu_exact(projected)
        self._record(trace, "clinical_encoder.projection_gelu_1", projected)
        projected = layer_norm(
            projected,
            self._parameter("clinical_encoder.projection.2.weight"),
            self._parameter("clinical_encoder.projection.2.bias"),
            eps=1e-5,
        )
        self._record(trace, "clinical_encoder.projection_layer_norm_1", projected)
        projected = linear(
            projected,
            self._parameter("clinical_encoder.projection.4.weight"),
            self._parameter("clinical_encoder.projection.4.bias"),
        )
        self._record(trace, "clinical_encoder.projection_linear_2", projected)
        projected = gelu_exact(projected)
        self._record(trace, "clinical_encoder.projection_gelu_2", projected)
        projected = layer_norm(
            projected,
            self._parameter("clinical_encoder.projection.6.weight"),
            self._parameter("clinical_encoder.projection.6.bias"),
            eps=1e-5,
        )
        self._record(trace, "clinical_encoder.output", projected)
        return projected

    def forward(
        self,
        batch: PreparedArrays,
        *,
        collect_trace: bool = False,
    ) -> tuple[Float32Array, dict[str, Float32Array]]:
        trace: dict[str, Float32Array] = {}
        pathology = self._feature_encoder(batch.pathology, "path_encoder", trace)
        query = np.expand_dims(pathology, axis=1)
        ct_tokens = np.stack(
            [
                self._feature_encoder(batch.ct_shape, "ct_shape_encoder", trace),
                self._feature_encoder(batch.ct_original, "ct_original_encoder", trace),
                self._feature_encoder(batch.ct_wavelet, "ct_wavelet_encoder", trace),
                self._feature_encoder(batch.ct_transformed, "ct_transformed_encoder", trace),
            ],
            axis=1,
        ).astype(np.float32)
        clinical = np.expand_dims(self._clinical_encoder(batch, trace), axis=1)
        context = np.concatenate([ct_tokens, clinical], axis=1).astype(np.float32)
        attended, attention_weights = multihead_attention(
            query,
            context,
            self._parameter("cross_attention.attention.in_proj_weight"),
            self._parameter("cross_attention.attention.in_proj_bias"),
            self._parameter("cross_attention.attention.out_proj.weight"),
            self._parameter("cross_attention.attention.out_proj.bias"),
            num_heads=4,
        )
        self._record(trace, "cross_attention.attended", attended)
        self._record(trace, "cross_attention.weights", attention_weights)
        enhanced = layer_norm(
            query + attended,
            self._parameter("cross_attention.normalization.weight"),
            self._parameter("cross_attention.normalization.bias"),
            eps=1e-5,
        )
        self._record(trace, "cross_attention.output", enhanced)
        fusion = np.concatenate([query[:, 0], enhanced[:, 0]], axis=1).astype(np.float32)
        classifier = linear(
            fusion,
            self._parameter("classifier.0.weight"),
            self._parameter("classifier.0.bias"),
        )
        self._record(trace, "classifier.linear_1", classifier)
        classifier = gelu_exact(classifier)
        self._record(trace, "classifier.gelu", classifier)
        classifier = layer_norm(
            classifier,
            self._parameter("classifier.2.weight"),
            self._parameter("classifier.2.bias"),
            eps=1e-5,
        )
        self._record(trace, "classifier.layer_norm", classifier)
        logits = linear(
            classifier,
            self._parameter("classifier.4.weight"),
            self._parameter("classifier.4.bias"),
        )
        self._record(trace, "classifier.logits", logits)
        return logits, trace if collect_trace else {}


__all__ = ["NumpyMCAT"]
