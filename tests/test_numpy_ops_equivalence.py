from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch", reason="Torch is a conversion-test dependency only")
from torch import nn  # noqa: E402


def test_linear_gelu_layer_norm_and_softmax_match_torch() -> None:
    from crc_lnm_mcp.inference.numpy_ops import gelu_exact, layer_norm, linear, softmax

    rng = np.random.default_rng(2024)
    x = rng.normal(size=(3, 11)).astype(np.float32)
    weight = rng.normal(size=(7, 11)).astype(np.float32)
    bias = rng.normal(size=(7,)).astype(np.float32)
    gamma = rng.normal(size=(7,)).astype(np.float32)
    beta = rng.normal(size=(7,)).astype(np.float32)
    torch_linear = torch.nn.functional.linear(
        torch.from_numpy(x), torch.from_numpy(weight), torch.from_numpy(bias)
    ).numpy()
    actual_linear = linear(x, weight, bias)
    np.testing.assert_allclose(actual_linear, torch_linear, atol=1e-6, rtol=1e-6)
    torch_gelu = torch.nn.functional.gelu(
        torch.from_numpy(actual_linear), approximate="none"
    ).numpy()
    actual_gelu = gelu_exact(actual_linear)
    np.testing.assert_allclose(actual_gelu, torch_gelu, atol=1e-6, rtol=1e-6)
    torch_norm = torch.nn.functional.layer_norm(
        torch.from_numpy(actual_gelu),
        (7,),
        torch.from_numpy(gamma),
        torch.from_numpy(beta),
        1e-5,
    ).numpy()
    actual_norm = layer_norm(actual_gelu, gamma, beta, eps=1e-5)
    np.testing.assert_allclose(actual_norm, torch_norm, atol=1e-5, rtol=1e-5)
    torch_softmax = torch.softmax(torch.from_numpy(actual_norm), dim=-1).numpy()
    np.testing.assert_allclose(softmax(actual_norm, axis=-1), torch_softmax, atol=1e-7, rtol=1e-6)


def test_fixed_multihead_attention_matches_torch_eval() -> None:
    from crc_lnm_mcp.inference.numpy_ops import multihead_attention

    rng = np.random.default_rng(7319)
    query = rng.normal(size=(2, 1, 128)).astype(np.float32)
    context = rng.normal(size=(2, 5, 128)).astype(np.float32)
    module = nn.MultiheadAttention(128, 4, dropout=0.2, batch_first=True).eval()
    with torch.inference_mode():
        expected, expected_weights = module(
            torch.from_numpy(query),
            torch.from_numpy(context),
            torch.from_numpy(context),
            need_weights=True,
            average_attn_weights=True,
        )
    actual, actual_weights = multihead_attention(
        query,
        context,
        module.in_proj_weight.detach().numpy(),
        module.in_proj_bias.detach().numpy(),
        module.out_proj.weight.detach().numpy(),
        module.out_proj.bias.detach().numpy(),
        num_heads=4,
    )
    np.testing.assert_allclose(actual, expected.numpy(), atol=1e-5, rtol=1e-5)
    np.testing.assert_allclose(actual_weights, expected_weights.numpy(), atol=1e-6, rtol=1e-6)
    assert actual.dtype == np.float32
