"""Development-only Torch reference for the archived seed_2024 architecture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn


@dataclass(frozen=True, slots=True)
class MultimodalBatch:
    pathology: torch.Tensor
    ct_shape: torch.Tensor
    ct_original: torch.Tensor
    ct_wavelet: torch.Tensor
    ct_transformed: torch.Tensor
    age: torch.Tensor
    male: torch.Tensor
    type_index: torch.Tensor
    t_stage_index: torch.Tensor


class FeatureEncoder(nn.Module):
    def __init__(self, input_dim: int, intermediate_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, intermediate_dim),
            nn.GELU(),
            nn.LayerNorm(intermediate_dim),
            nn.Dropout(dropout),
            nn.Linear(intermediate_dim, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)


class ClinicalEncoder(nn.Module):
    def __init__(
        self, type_vocab_size: int, t_stage_vocab_size: int, hidden_dim: int, dropout: float
    ):
        super().__init__()
        self.type_embedding = nn.Embedding(type_vocab_size, 4)
        self.t_stage_embedding = nn.Embedding(t_stage_vocab_size, 4)
        self.continuous_encoder = nn.Sequential(nn.Linear(2, 16), nn.GELU(), nn.LayerNorm(16))
        self.projection = nn.Sequential(
            nn.Linear(24, 64),
            nn.GELU(),
            nn.LayerNorm(64),
            nn.Dropout(dropout),
            nn.Linear(64, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
        )

    def forward(self, batch: MultimodalBatch) -> torch.Tensor:
        continuous = self.continuous_encoder(torch.cat([batch.age, batch.male], dim=1))
        return self.projection(
            torch.cat(
                [
                    continuous,
                    self.type_embedding(batch.type_index),
                    self.t_stage_embedding(batch.t_stage_index),
                ],
                dim=1,
            )
        )


class MCATTabular(nn.Module):
    def __init__(
        self,
        *,
        type_vocab_size: int,
        t_stage_vocab_size: int,
        hidden_dim: int,
        num_heads: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.path_encoder = FeatureEncoder(768, 256, hidden_dim, dropout)
        self.ct_shape_encoder = FeatureEncoder(14, 64, hidden_dim, dropout)
        self.ct_original_encoder = FeatureEncoder(93, 128, hidden_dim, dropout)
        self.ct_wavelet_encoder = FeatureEncoder(744, 256, hidden_dim, dropout)
        self.ct_transformed_encoder = FeatureEncoder(558, 256, hidden_dim, dropout)
        self.clinical_encoder = ClinicalEncoder(
            type_vocab_size, t_stage_vocab_size, hidden_dim, dropout
        )
        self.attention = nn.MultiheadAttention(
            hidden_dim, num_heads, dropout=dropout, batch_first=True
        )
        self.attention_norm = nn.LayerNorm(hidden_dim)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.GELU(),
            nn.LayerNorm(64),
            nn.Dropout(dropout),
            nn.Linear(64, 2),
        )

    def forward(self, batch: MultimodalBatch) -> torch.Tensor:
        pathology = self.path_encoder(batch.pathology)
        query = pathology.unsqueeze(1)
        ct_tokens = torch.stack(
            [
                self.ct_shape_encoder(batch.ct_shape),
                self.ct_original_encoder(batch.ct_original),
                self.ct_wavelet_encoder(batch.ct_wavelet),
                self.ct_transformed_encoder(batch.ct_transformed),
            ],
            dim=1,
        )
        clinical = self.clinical_encoder(batch).unsqueeze(1)
        context = torch.cat([ct_tokens, clinical], dim=1)
        attended, _weights = self.attention(query, context, context)
        enhanced = self.attention_norm(query + attended)
        return self.classifier(torch.cat([query[:, 0], enhanced[:, 0]], dim=1))


def build_model(config: dict[str, Any]) -> MCATTabular:
    model = MCATTabular(
        type_vocab_size=int(config["type_vocab_size"]),
        t_stage_vocab_size=int(config["t_stage_vocab_size"]),
        hidden_dim=int(config["hidden_dim"]),
        num_heads=int(config["num_heads"]),
        dropout=float(config["dropout"]),
    )
    return model


def remap_state_dict(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {
        key.replace("cross_attention.attention", "attention").replace(
            "cross_attention.normalization", "attention_norm"
        ): value
        for key, value in state.items()
    }


__all__ = ["MultimodalBatch", "build_model", "remap_state_dict"]
