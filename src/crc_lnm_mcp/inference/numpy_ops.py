"""Model-specific float32 NumPy operators matching the archived Torch graph."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

Float32Array = NDArray[np.float32]


def _float32(value: NDArray[np.generic]) -> Float32Array:
    return np.asarray(value, dtype=np.float32)


def linear(x: Float32Array, weight: Float32Array, bias: Float32Array) -> Float32Array:
    return _float32(np.matmul(x, weight.T) + bias)


def gelu_exact(x: Float32Array) -> Float32Array:
    values = np.asarray(x, dtype=np.float32)
    scaled = values.astype(np.float64) / math.sqrt(2.0)
    erf = np.fromiter(
        (math.erf(float(value)) for value in scaled.flat),
        dtype=np.float64,
        count=scaled.size,
    ).reshape(values.shape)
    return _float32(0.5 * values.astype(np.float64) * (1.0 + erf))


def layer_norm(
    x: Float32Array,
    weight: Float32Array,
    bias: Float32Array,
    *,
    eps: float,
) -> Float32Array:
    values = np.asarray(x, dtype=np.float32)
    mean = np.mean(values, axis=-1, keepdims=True, dtype=np.float32)
    centered = values - mean
    variance = np.mean(centered * centered, axis=-1, keepdims=True, dtype=np.float32)
    normalized = centered / np.sqrt(variance + np.float32(eps), dtype=np.float32)
    return _float32(normalized * weight + bias)


def softmax(x: Float32Array, *, axis: int) -> Float32Array:
    values = np.asarray(x, dtype=np.float32)
    shifted = values - np.max(values, axis=axis, keepdims=True)
    exponentials = np.exp(shifted, dtype=np.float32)
    return _float32(exponentials / np.sum(exponentials, axis=axis, keepdims=True))


def multihead_attention(
    query: Float32Array,
    context: Float32Array,
    in_proj_weight: Float32Array,
    in_proj_bias: Float32Array,
    out_proj_weight: Float32Array,
    out_proj_bias: Float32Array,
    *,
    num_heads: int,
) -> tuple[Float32Array, Float32Array]:
    embed_dim = int(query.shape[-1])
    if context.shape[-1] != embed_dim or embed_dim % num_heads:
        raise ValueError("attention dimensions are invalid")
    head_dim = embed_dim // num_heads
    q_weight, k_weight, v_weight = np.split(in_proj_weight, 3, axis=0)
    q_bias, k_bias, v_bias = np.split(in_proj_bias, 3, axis=0)
    q = linear(query, q_weight, q_bias)
    k = linear(context, k_weight, k_bias)
    v = linear(context, v_weight, v_bias)

    def split_heads(values: Float32Array) -> Float32Array:
        batch, length, _width = values.shape
        return _float32(values.reshape(batch, length, num_heads, head_dim).transpose(0, 2, 1, 3))

    q_heads = split_heads(q)
    k_heads = split_heads(k)
    v_heads = split_heads(v)
    scores = _float32(
        np.matmul(q_heads, k_heads.transpose(0, 1, 3, 2)) / np.float32(math.sqrt(head_dim))
    )
    weights = softmax(scores, axis=-1)
    attended = np.matmul(weights, v_heads)
    merged = attended.transpose(0, 2, 1, 3).reshape(query.shape[0], query.shape[1], embed_dim)
    output = linear(_float32(merged), out_proj_weight, out_proj_bias)
    return output, _float32(np.mean(weights, axis=1, dtype=np.float32))


__all__ = ["gelu_exact", "layer_norm", "linear", "multihead_attention", "softmax"]
