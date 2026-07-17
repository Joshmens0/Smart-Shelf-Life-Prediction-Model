"""
image_backbone.py
-----------------
Image branch of the multimodal mango shelf-life prediction model.

Provides:
    MangoImageDataset  — PyTorch Dataset for loading mango images with labels.
    ImageBackbone      — Pretrained EfficientNet-B0 feature extractor with a
                         configurable projection head for multimodal fusion.

Usage
-----
>>> from image_backbone import ImageBackbone, MangoImageDataset, get_train_transforms
>>>
>>> records = [{'image_path': 'data/.../img.png', 'days_remaining': 6}]
>>> dataset = MangoImageDataset(records, transform=get_train_transforms())
>>> model   = ImageBackbone(output_dim=256, freeze_base=True)
"""

import logging
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import Dataset
from torchvision import models, transforms
from torchvision.models import EfficientNet_B0_Weights

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

IMAGE_SIZE: int = 224  # EfficientNet-B0 native input resolution

# Standard ImageNet statistics — required when using pretrained weights
_IMAGENET_MEAN: list[float] = [0.485, 0.456, 0.406]
_IMAGENET_STD:  list[float] = [0.229, 0.224, 0.225]


# ------------------------------------------------------------------
# Transforms
# ------------------------------------------------------------------

def get_train_transforms() -> transforms.Compose:
    """
    Augmented transform pipeline for training.

    Applies random flips, cropping, rotation, and colour jitter to improve
    generalisation on the relatively small mango dataset.
    """
    return transforms.Compose([
        transforms.RandomResizedCrop((IMAGE_SIZE, IMAGE_SIZE), scale=(0.8, 1.0)),
        transforms.RandomRotation(degrees=15),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.ColorJitter(
            brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05
        ),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


def get_eval_transforms() -> transforms.Compose:
    """
    Deterministic transform pipeline for validation and inference.
    No augmentation — only resize and normalise.
    """
    return transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


# ------------------------------------------------------------------
# Dataset
# ------------------------------------------------------------------

class MangoImageDataset(Dataset):
    """
    PyTorch Dataset for mango shelf-life images.

    Each record must contain:
        - 'image_path'    (str | Path) : Path to the mango image.
        - 'days_remaining' (int | float): Regression target — days left before spoilage.

    Args:
        records   : List of dicts with the fields described above.
        transform : torchvision transforms applied to every loaded image.
                    Defaults to eval transforms if not provided.
    """

    def __init__(
        self,
        records: list[dict],
        transform: Optional[transforms.Compose] = None,
    ) -> None:
        self._records   = records
        self._transform = transform or get_eval_transforms()
        logger.info(
            "MangoImageDataset ready — %d sample(s).", len(records)
        )

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            image  : Float tensor of shape (3, IMAGE_SIZE, IMAGE_SIZE).
            label  : Scalar float tensor — days_remaining.
        """
        record     = self._records[idx]
        image_path = Path(record['image_path'])

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}. "
                "Ensure update_metadata_images() has been called."
            )

        image = Image.open(image_path).convert('RGB')
        image = self._transform(image)
        label = torch.tensor(record['days_remaining'], dtype=torch.float32)

        return image, label


# ------------------------------------------------------------------
# Model
# ------------------------------------------------------------------

class ImageBackbone(nn.Module):
    """
    Pretrained EfficientNet-B0 image feature extractor.

    The original classifier head is replaced with a two-layer projection
    that maps visual features to a fixed-size embedding vector, ready for
    concatenation with the tabular branch in the fusion model.

    Architecture
    ------------
    EfficientNet-B0 features (frozen)
        → Dropout(0.3)
        → Linear(1280 → output_dim)
        → ReLU

    Args:
        output_dim   : Dimension of the output feature embedding (default: 256).
        freeze_base  : If True, pretrained convolutional layers are frozen and
                       only the projection head is trained. Set to False for
                       full fine-tuning (requires more data / longer training).
    """

    def __init__(
        self,
        output_dim: int = 256,
        freeze_base: bool = True,
        unfreeze_last_blocks: bool = True,
    ) -> None:
        super().__init__()

        # Load EfficientNet-B0 with pretrained ImageNet weights
        base        = models.efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        in_features = base.classifier[1].in_features  # 1280 for EfficientNet-B0

        # Freeze pretrained convolutional layers when requested
        if freeze_base:
            for param in base.features.parameters():
                param.requires_grad = False
            
            # Unfreeze only the final deep layers (Block 7 & 8)
            if unfreeze_last_blocks:
                for param in base.features[7].parameters():
                    param.requires_grad = True
                for param in base.features[8].parameters():
                    param.requires_grad = True
                logger.info("ImageBackbone: base is frozen, but Block 7 & 8 are unfrozen.")
            else:
                logger.info("ImageBackbone: pretrained feature layers are frozen.")

        # Replace the default classifier with a projection head
        base.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, output_dim),
            nn.ReLU(inplace=True),
        )

        self.backbone   = base
        self.output_dim = output_dim

        logger.info(
            "ImageBackbone initialised — output_dim=%d, freeze_base=%s, unfreeze_last_blocks=%s.",
            output_dim, freeze_base, unfreeze_last_blocks,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Batch of pre-processed images — shape (B, 3, H, W).

        Returns:
            Feature tensor of shape (B, output_dim).
        """
        return self.backbone(x)

    def trainable_params(self) -> int:
        """Returns the number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def total_params(self) -> int:
        """Returns the total number of parameters."""
        return sum(p.numel() for p in self.parameters())


# ------------------------------------------------------------------
# Smoke test
# ------------------------------------------------------------------

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    )

    print("=" * 55)
    print("  ImageBackbone — Smoke Test")
    print("=" * 55)

    model = ImageBackbone(output_dim=256, freeze_base=True)
    model.eval()

    # Synthetic batch: 4 images, 3 channels, 224×224
    dummy_batch = torch.randn(4, 3, IMAGE_SIZE, IMAGE_SIZE)

    with torch.no_grad():
        features = model(dummy_batch)

    print(f"\nInput  shape : {list(dummy_batch.shape)}")
    print(f"Output shape : {list(features.shape)}")
    print(f"\nTotal params     : {model.total_params():>10,}")
    print(f"Trainable params : {model.trainable_params():>10,}")
    print(f"Frozen params    : {model.total_params() - model.trainable_params():>10,}")
