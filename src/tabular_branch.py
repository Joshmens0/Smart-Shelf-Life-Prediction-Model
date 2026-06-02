"""
tabular_branch.py
-----------------
Tabular branch of the multimodal mango shelf-life prediction model.

Handles the environmental sensor features available at INFERENCE TIME.

Design rationale
----------------
Destructive physicochemical measurements (brix, pH, texture, weight loss,
ripeness index) are collected during research to produce accurate
``days_remaining`` labels, but they CANNOT be collected by the end user
without destroying the mango.

Only the following are available at inference time:
    Temperature  (°C)        — from a thermometer / sensor
    Humidity     (%)         — from a humidity sensor
    Environment  (category)  — ambient or cold-storage (user-selectable)

Feature layout
--------------
Numerical (2) : Temperature, Humidity
Categorical (1): Environment → ['ambient', 'controlled']

Provides:
    TabularFeatureEncoder  — Encodes categorical + numerical inputs.
    TabularBranch          — MLP projecting to a fixed-size embedding.

Usage
-----
>>> encoder = TabularFeatureEncoder()
>>> branch  = TabularBranch(input_dim=encoder.output_dim, output_dim=64)
>>>
>>> batch   = encoder(records)   # list[dict] → FloatTensor (B, output_dim)
>>> embed   = branch(batch)      # (B, 64)
"""

import logging
from typing import Optional

import torch
import torch.nn as nn
import pandas as pd

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Vocabulary definitions
# ------------------------------------------------------------------

ENVIRONMENT_VOCAB: dict[str, int] = {
    'ambient':    0,
    'controlled': 1,
    'unknown':    2,   # fallback
}

# Inference-time numerical inputs (what the end user provides)
NUMERICAL_COLS: list[str] = [
    'Temperature',
    'Humidity',
]

# Inference-time categorical inputs
CATEGORICAL_COLS: dict[str, dict[str, int]] = {
    'Environment': ENVIRONMENT_VOCAB,
}

# Embedding dimension for each categorical feature
EMBEDDING_DIM: int = 4


# ------------------------------------------------------------------
# Feature encoder
# ------------------------------------------------------------------

class TabularFeatureEncoder(nn.Module):
    """
    Converts a batch of tabular records into a single flat feature tensor.

    Categorical columns are mapped through learned embeddings.
    Numerical columns are passed through as-is (normalisation should be
    applied upstream via StandardScaler before training).

    Attributes:
        output_dim (int): Total dimension of the output feature vector.
                          = len(NUMERICAL_COLS) + len(CATEGORICAL_COLS) * EMBEDDING_DIM
    """

    def __init__(self) -> None:
        super().__init__()

        # One Embedding layer per categorical column
        self._embeddings = nn.ModuleDict({
            col: nn.Embedding(
                num_embeddings=len(vocab),
                embedding_dim=EMBEDDING_DIM,
                padding_idx=None,
            )
            for col, vocab in CATEGORICAL_COLS.items()
        })

        self.output_dim: int = (
            len(NUMERICAL_COLS) + len(CATEGORICAL_COLS) * EMBEDDING_DIM
        )
        logger.info(
            "TabularFeatureEncoder ready — output_dim=%d "
            "(%d numerical + %d categorical × %d embedding_dim).",
            self.output_dim,
            len(NUMERICAL_COLS),
            len(CATEGORICAL_COLS),
            EMBEDDING_DIM,
        )

    def forward(self, records: list[dict]) -> torch.Tensor:
        """
        Args:
            records: List of dicts, each representing one DataFrame row.
                     All columns in NUMERICAL_COLS and CATEGORICAL_COLS
                     must be present.

        Returns:
            Float tensor of shape (B, output_dim).
        """
        numerical_parts: list[torch.Tensor] = []
        categorical_parts: list[torch.Tensor] = []

        # --- Numerical features ---
        for col in NUMERICAL_COLS:
            values = [float(r.get(col) or 0.0) for r in records]
            numerical_parts.append(
                torch.tensor(values, dtype=torch.float32).unsqueeze(1)
            )
        numerical_tensor = torch.cat(numerical_parts, dim=1)  # (B, 17)

        # --- Categorical features (embeddings) ---
        for col, vocab in CATEGORICAL_COLS.items():
            raw = [str(r.get(col, 'unknown')).lower() for r in records]
            # Map unknown tokens to the last index (fallback)
            fallback = len(vocab) - 1
            indices  = [vocab.get(v, fallback) for v in raw]
            idx_tensor = torch.tensor(indices, dtype=torch.long)
            embed      = self._embeddings[col](idx_tensor)  # (B, EMBEDDING_DIM)
            categorical_parts.append(embed)

        categorical_tensor = torch.cat(categorical_parts, dim=1)  # (B, 8)

        return torch.cat([numerical_tensor, categorical_tensor], dim=1)  # (B, output_dim)


# ------------------------------------------------------------------
# Tabular MLP branch
# ------------------------------------------------------------------

class TabularBranch(nn.Module):
    """
    MLP that maps a flat tabular feature vector to a fixed-size embedding.

    Architecture
    ------------
    Input (input_dim)
        → Linear → BatchNorm1d → ReLU → Dropout
        → Linear → BatchNorm1d → ReLU → Dropout
        → Linear (output_dim) → ReLU

    The output embedding is concatenated with the image embedding in the
    fusion model to jointly predict ``days_remaining``.

    Args:
        input_dim  : Dimension of the input feature vector.
                     Use TabularFeatureEncoder.output_dim.
        output_dim : Size of the output embedding vector (default: 128).
        hidden_dim : Width of the two hidden layers (default: 128).
        dropout    : Dropout probability applied after each hidden layer.
    """

    def __init__(
        self,
        input_dim:  int,
        output_dim: int   = 128,
        hidden_dim: int   = 128,
        dropout:    float = 0.3,
    ) -> None:
        super().__init__()

        self.output_dim = output_dim

        self.net = nn.Sequential(
            # Hidden layer 1
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),

            # Hidden layer 2
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),

            # Projection to output embedding
            nn.Linear(hidden_dim, output_dim),
            nn.ReLU(inplace=True),
        )

        logger.info(
            "TabularBranch initialised — input_dim=%d, hidden_dim=%d, output_dim=%d.",
            input_dim, hidden_dim, output_dim,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Encoded tabular features — shape (B, input_dim).

        Returns:
            Embedding tensor of shape (B, output_dim).
        """
        return self.net(x)

    def trainable_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ------------------------------------------------------------------
# Smoke test
# ------------------------------------------------------------------

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    )

    print("=" * 55)
    print("  TabularBranch — Smoke Test")
    print("=" * 55)

    # Simulate a batch of 4 inference-time records (image + temp + humidity)
    dummy_records = [
        {
            'Environment': 'ambient',
            'Temperature': 25.0,
            'Humidity':    65.0,
        }
    ] * 4

    encoder = TabularFeatureEncoder()
    branch  = TabularBranch(input_dim=encoder.output_dim, output_dim=64)
    branch.eval()

    with torch.no_grad():
        features  = encoder(dummy_records)
        embedding = branch(features)

    print(f"\nEncoded features shape : {list(features.shape)}")
    print(f"Embedding shape        : {list(embedding.shape)}")
    print(f"Trainable params       : {branch.trainable_params():,}")
    print(f"\nSample embedding (first 6 dims): {embedding[0, :6].tolist()}")
