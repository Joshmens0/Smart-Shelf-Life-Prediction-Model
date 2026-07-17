"""
fusion_model.py
---------------
Full multimodal shelf-life prediction model for mango freshness assessment.

Fuses visual features (EfficientNet-B0) with environmental sensor data
(Temperature, Humidity, Environment) to regress ``days_remaining``.

Inference-time inputs
---------------------
  Image (3 × 224 × 224)    — Photo of the mango (camera / phone)
  Temperature (float, °C)  — Ambient thermometer reading
  Humidity    (float, %)   — Humidity sensor reading
  Environment (str)        — 'ambient' or 'controlled' (user-selected)

Note: Destructive measurements (brix, pH, texture, weight_loss,
ripeness_index) are used only to build accurate training labels.
They are NOT model inputs and are NOT needed at inference time.

Architecture
------------
                                              ┌─────────────────────┐
  Image (3 × 224 × 224) ──► ImageBackbone ──►│                     │
                               (256-dim)      │  Concatenate (320)  │──► Fusion Head ──► days_remaining
  Sensor data (6 features) ──► TabularBranch►│                     │
                                (64-dim)      └─────────────────────┘

Fusion Head
-----------
  Linear(320, 128) → BatchNorm → ReLU → Dropout(0.3)
  Linear(128,  32) → BatchNorm → ReLU → Dropout(0.2)
  Linear( 32,   1) → scalar regression output

Provides:
    MultimodalDataset        — PyTorch Dataset pairing images with sensor records.
    MultimodalShelfLifeModel — Full model wiring all three branches.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from image_backbone import ImageBackbone, get_eval_transforms, get_train_transforms
from tabular_branch import CATEGORICAL_COLS, NUMERICAL_COLS, TabularBranch, TabularFeatureEncoder

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

class MultimodalDataset(Dataset):
    """
    PyTorch Dataset that yields (image_tensor, tabular_record, label) triples.

    Reads rows from the preprocessed DataFrame produced by
    ``convert_to_data_frame.py``.  Each row must contain:
        - 'Image Path'      (str)   : Relative path to the mango image.
        - 'days_remaining'  (float) : Regression target.
        - All columns in NUMERICAL_COLS and CATEGORICAL_COLS.

    Args:
        dataframe : Preprocessed pandas DataFrame.
        transform : Image transforms. Defaults to eval transforms.
        root_dir  : Working directory prepended to relative image paths.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame,
        transform: Optional[transforms.Compose] = None,
        root_dir:  str = '.',
    ) -> None:
        # Validate required columns are present (including auxiliary biochemical targets)
        aux_cols = {'Brix Mean', 'pH Mean', 'Texture Mean'}
        required = {'Image Path', 'days_remaining'} | set(NUMERICAL_COLS) | set(CATEGORICAL_COLS) | aux_cols
        missing  = required - set(dataframe.columns)
        if missing:
            raise ValueError(
                f"DataFrame is missing required columns: {missing}"
            )

        self._df        = dataframe.reset_index(drop=True)
        self._transform = transform or get_eval_transforms()
        self._root_dir  = Path(root_dir)

        logger.info(
            "MultimodalDataset ready — %d sample(s), root_dir='%s'.",
            len(self._df), self._root_dir,
        )

    def __len__(self) -> int:
        return len(self._df)

    def __getitem__(
        self, idx: int
    ) -> tuple[torch.Tensor, dict, torch.Tensor]:
        """
        Returns:
            image   : Float tensor  — shape (3, 224, 224).
            tabular : Dict of column_name → value for this row.
            label   : Scalar float tensor — days_remaining.
        """
        row = self._df.iloc[idx]

        # --- Image ---
        image_path = self._root_dir / str(row['Image Path'])
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        image = Image.open(image_path).convert('RGB')
        image = self._transform(image)

        # --- Tabular record ---
        tabular = row.to_dict()

        # --- Label / Target (days_remaining) ---
        label = torch.tensor(float(row['days_remaining']), dtype=torch.float32)

        # --- Privileged Biochemical Data (LUPI) ---
        privileged = torch.tensor([
            float(row['Brix Mean']),
            float(row['pH Mean']),
            float(row['Texture Mean'])
        ], dtype=torch.float32)

        return image, tabular, label, privileged


def collate_multimodal(
    batch: list[tuple[torch.Tensor, dict, torch.Tensor, torch.Tensor]]
) -> tuple[torch.Tensor, list[dict], torch.Tensor, torch.Tensor]:
    """
    Custom collate_fn for DataLoader.

    Stacks images, labels, and privileged vectors.
    """
    images     = torch.stack([item[0] for item in batch])
    tabulars   = [item[1] for item in batch]
    labels     = torch.stack([item[2] for item in batch])
    privileged = torch.stack([item[3] for item in batch])
    return images, tabulars, labels, privileged


# ------------------------------------------------------------------
# Full multimodal model
# ------------------------------------------------------------------

class MultimodalShelfLifeModel(nn.Module):
    """
    End-to-end multimodal model for mango shelf-life regression.

    Wires the image backbone, tabular encoder+branch, and fusion head
    into a single forward pass.

    Args:
        img_output_dim  : Output embedding size from ImageBackbone (default: 256).
        tab_output_dim  : Output embedding size from TabularBranch  (default: 64).
        freeze_backbone : Freeze EfficientNet pretrained layers (default: True).
        dropout_fusion  : Dropout in the fusion head layers.
    """

    def __init__(
        self,
        img_output_dim:  int   = 256,
        tab_output_dim:  int   = 64,
        freeze_backbone: bool  = True,
        unfreeze_last_blocks: bool = True,
        dropout_fusion:  float = 0.3,
    ) -> None:
        super().__init__()

        # ── Image branch ──────────────────────────────────────────────
        self.image_branch = ImageBackbone(
            output_dim=img_output_dim,
            freeze_base=freeze_backbone,
            unfreeze_last_blocks=unfreeze_last_blocks,
        )

        # ── Tabular branch (sensor data only) ─────────────────────────
        self.tabular_encoder = TabularFeatureEncoder()
        self.tabular_branch  = TabularBranch(
            input_dim=self.tabular_encoder.output_dim,
            output_dim=tab_output_dim,
        )

        # ── Fusion head ───────────────────────────────────────────────
        fusion_input_dim = img_output_dim + tab_output_dim  # 320

        self.fusion_head = nn.Sequential(
            nn.Linear(fusion_input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_fusion),

            nn.Linear(128, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_fusion * 0.67),  # ~0.2

            nn.Linear(32, 1),   # regression: scalar output (days_remaining)
        )

        logger.info(
            "MultimodalShelfLifeModel (Student) initialised — "
            "img_dim=%d, tab_dim=%d, fusion_input=%d.",
            img_output_dim, tab_output_dim, fusion_input_dim,
        )

    def forward(
        self,
        images:   torch.Tensor,
        tabulars: list[dict],
    ) -> torch.Tensor:
        """
        Args:
            images   : Batch of pre-processed images — shape (B, 3, 224, 224).
            tabulars : List of B tabular record dicts.

        Returns:
            Predicted days_remaining — shape (B,).
        """
        # Image branch: (B, 3, H, W) → (B, img_output_dim)
        img_embed = self.image_branch(images)

        # Tabular branch: list[dict] → (B, input_dim) → (B, tab_output_dim)
        tab_features = self.tabular_encoder(tabulars)
        tab_embed    = self.tabular_branch(tab_features)

        # Fusion: concat → (B, fusion_input_dim)
        fused = torch.cat([img_embed, tab_embed], dim=1)

        # Regression head: (B, fusion_input_dim) → (B,)
        prediction = self.fusion_head(fused).squeeze(1)

        return prediction

    def trainable_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def total_params(self) -> int:
        return sum(p.numel() for p in self.parameters())


# ------------------------------------------------------------------
# Teacher Model (Privileged Information Branch)
# ------------------------------------------------------------------

class TeacherMultimodalModel(nn.Module):
    """
    Teacher model that has access to both non-destructive inputs (Image, Tabular)
    AND privileged biological variables (Brix Mean, pH Mean, Texture Mean).
    """

    def __init__(
        self,
        img_output_dim:  int = 256,
        tab_output_dim:  int = 64,
        bio_output_dim:  int = 64,
        freeze_backbone: bool = True,
        unfreeze_last_blocks: bool = True,
        dropout_fusion:  float = 0.3,
    ) -> None:
        super().__init__()

        # Image branch
        self.image_branch = ImageBackbone(
            output_dim=img_output_dim,
            freeze_base=freeze_backbone,
            unfreeze_last_blocks=unfreeze_last_blocks,
        )

        # Tabular branch
        self.tabular_encoder = TabularFeatureEncoder()
        self.tabular_branch  = TabularBranch(
            input_dim=self.tabular_encoder.output_dim,
            output_dim=tab_output_dim,
        )

        # Privileged biochemical branch (3 inputs -> MLP -> 64-dim)
        self.bio_branch = nn.Sequential(
            nn.Linear(3, bio_output_dim),
            nn.BatchNorm1d(bio_output_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_fusion * 0.5),
        )

        # Fusion head (fuses image + tabular + bio embeddings)
        fusion_input_dim = img_output_dim + tab_output_dim + bio_output_dim  # 256 + 64 + 64 = 384

        self.fusion_head = nn.Sequential(
            nn.Linear(fusion_input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_fusion),

            nn.Linear(128, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_fusion * 0.67),

            nn.Linear(32, 1),  # regression scalar output
        )

        logger.info(
            "TeacherMultimodalModel (Privileged) initialised — "
            "img_dim=%d, tab_dim=%d, bio_dim=%d, fusion_input=%d.",
            img_output_dim, tab_output_dim, bio_output_dim, fusion_input_dim,
        )

    def forward(
        self,
        images:     torch.Tensor,
        tabulars:   list[dict],
        privileged: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            images: (B, 3, 224, 224)
            tabulars: List of B dicts
            privileged: (B, 3) tensor of Brix Mean, pH Mean, Texture Mean
        """
        img_embed = self.image_branch(images)

        tab_features = self.tabular_encoder(tabulars)
        tab_embed    = self.tabular_branch(tab_features)

        bio_embed    = self.bio_branch(privileged)

        fused = torch.cat([img_embed, tab_embed, bio_embed], dim=1)
        prediction = self.fusion_head(fused).squeeze(1)

        return prediction

    def trainable_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def total_params(self) -> int:
        return sum(p.numel() for p in self.parameters())


# ------------------------------------------------------------------
# Smoke test
# ------------------------------------------------------------------

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    )

    # Smoke test Student
    print("=" * 60)
    print("  MultimodalShelfLifeModel (Student) — Smoke Test")
    print("=" * 60)

    student = MultimodalShelfLifeModel(
        img_output_dim=256,
        tab_output_dim=128,
        freeze_backbone=True,
    )
    student.eval()

    BATCH = 4
    dummy_images = torch.randn(BATCH, 3, 224, 224)
    dummy_tabular = [
        {
            'Environment': 'ambient',
            'Temperature': 25.0,
            'Humidity':    65.0,
        }
    ] * BATCH

    with torch.no_grad():
        student_preds = student(dummy_images, dummy_tabular)

    print(f"\nStudent Output Shape  : {list(student_preds.shape)}")
    print(f"Student Predictions   : {student_preds.tolist()}")

    # Smoke test Teacher
    print("\n" + "=" * 60)
    print("  TeacherMultimodalModel (Privileged) — Smoke Test")
    print("=" * 60)

    teacher = TeacherMultimodalModel(
        img_output_dim=256,
        tab_output_dim=128,
        bio_output_dim=64,
        freeze_backbone=True,
    )
    teacher.eval()

    dummy_privileged = torch.randn(BATCH, 3)  # Brix, pH, Texture Mean

    with torch.no_grad():
        teacher_preds = teacher(dummy_images, dummy_tabular, dummy_privileged)

    print(f"\nTeacher Output Shape  : {list(teacher_preds.shape)}")
    print(f"Teacher Predictions   : {teacher_preds.tolist()}")

    print(f"\nStudent total parameters: {student.total_params():,}")
    print(f"Student trainable parameters: {student.trainable_params():,}")
    print(f"Teacher total parameters: {teacher.total_params():,}")
    print(f"Teacher trainable parameters: {teacher.trainable_params():,}")
