"""
train.py
--------
Training and evaluation scaffold for the multimodal mango shelf-life model.

Responsibilities:
    - Load and split the preprocessed DataFrame into train / validation sets.
    - Instantiate MultimodalDataset with appropriate transforms.
    - Run the training loop with logging, checkpointing, and early stopping.
    - Report MAE and RMSE on the validation set after each epoch.

Usage
-----
    python src/train.py

Expected files:
    preprocessed_data.csv    — Output of convert_to_data_frame.py.
    config.yaml              — Project-wide hyperparameter config.
"""

import logging
import math
import time
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
import yaml
from torch.utils.data import DataLoader, random_split

from fusion_model import MultimodalDataset, MultimodalShelfLifeModel, collate_multimodal
from image_backbone import get_eval_transforms, get_train_transforms

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

CONFIG_PATH = Path('config.yaml')
DATA_CSV    = Path('preprocessed_data.csv')
CKPT_DIR    = Path('checkpoints')


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

def compute_mae(preds: torch.Tensor, targets: torch.Tensor) -> float:
    """Mean Absolute Error — interpretable in days."""
    return (preds - targets).abs().mean().item()


def compute_rmse(preds: torch.Tensor, targets: torch.Tensor) -> float:
    """Root Mean Squared Error — penalises large errors more heavily."""
    return math.sqrt(((preds - targets) ** 2).mean().item())


# ------------------------------------------------------------------
# Training loop
# ------------------------------------------------------------------

def train_one_epoch(
    model:      MultimodalShelfLifeModel,
    loader:     DataLoader,
    optimizer:  torch.optim.Optimizer,
    criterion:  nn.Module,
    device:     torch.device,
) -> float:
    """Runs one full training epoch. Returns average training loss."""
    model.train()
    total_loss = 0.0

    for images, tabulars, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        predictions = model(images, tabulars)
        loss        = criterion(predictions, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(labels)

    return total_loss / len(loader.dataset)


@torch.no_grad()
def evaluate(
    model:     MultimodalShelfLifeModel,
    loader:    DataLoader,
    criterion: nn.Module,
    device:    torch.device,
) -> tuple[float, float, float]:
    """
    Evaluates the model on a DataLoader.

    Returns:
        (avg_loss, mae, rmse)
    """
    model.eval()
    total_loss  = 0.0
    all_preds   = []
    all_targets = []

    for images, tabulars, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        preds = model(images, tabulars)
        loss  = criterion(preds, labels)

        total_loss  += loss.item() * len(labels)
        all_preds.append(preds.cpu())
        all_targets.append(labels.cpu())

    all_preds   = torch.cat(all_preds)
    all_targets = torch.cat(all_targets)

    avg_loss = total_loss / len(loader.dataset)
    mae      = compute_mae(all_preds, all_targets)
    rmse     = compute_rmse(all_preds, all_targets)

    return avg_loss, mae, rmse


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> None:
    config = load_config()

    logging.basicConfig(
        level=getattr(logging, config['logging']['level'], logging.INFO),
        format=config['logging']['format'],
    )

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info("Using device: %s", device)

    # ── Load data ─────────────────────────────────────────────────
    if not DATA_CSV.exists():
        raise FileNotFoundError(
            f"'{DATA_CSV}' not found. "
            "Run convert_to_data_frame.py first to generate the CSV."
        )

    df = pd.read_csv(DATA_CSV)

    if 'days_remaining' not in df.columns:
        raise ValueError(
            "'days_remaining' column missing from the CSV. "
            "Ensure it is present in your JSON metadata files."
        )

    logger.info("Loaded dataset: %d rows.", len(df))

    # ── Train / validation split (80 / 20) ───────────────────────
    val_size   = max(1, int(0.2 * len(df)))
    train_size = len(df) - val_size

    # Reproducible split — change seed in config later if needed
    train_df = df.iloc[:train_size].reset_index(drop=True)
    val_df   = df.iloc[train_size:].reset_index(drop=True)

    logger.info("Split: %d train / %d validation.", train_size, val_size)

    # ── Datasets & loaders ────────────────────────────────────────
    train_dataset = MultimodalDataset(
        train_df, transform=get_train_transforms()
    )
    val_dataset = MultimodalDataset(
        val_df, transform=get_eval_transforms()
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=8,
        shuffle=True,
        collate_fn=collate_multimodal,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=8,
        shuffle=False,
        collate_fn=collate_multimodal,
        num_workers=0,
    )

    # ── Model ─────────────────────────────────────────────────────
    img_cfg = config['image_model']
    tab_cfg = config['tabular_model']

    model = MultimodalShelfLifeModel(
        img_output_dim=img_cfg['output_dim'],
        tab_output_dim=tab_cfg['output_dim'],
        freeze_backbone=img_cfg['freeze_base'],
        dropout_fusion=0.3,
    ).to(device)

    logger.info(
        "Model ready — trainable params: %d / %d.",
        model.trainable_params(), model.total_params(),
    )

    # ── Loss, optimiser, scheduler ────────────────────────────────
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=1e-3,
        weight_decay=1e-4,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5,
    )

    # ── Training ──────────────────────────────────────────────────
    EPOCHS        = 50
    PATIENCE      = 10
    best_val_loss = float('inf')
    no_improve    = 0

    CKPT_DIR.mkdir(exist_ok=True)

    print(f"\n{'Epoch':>6}  {'Train Loss':>11}  {'Val Loss':>10}  {'MAE':>7}  {'RMSE':>7}  {'Time':>7}")
    print("-" * 62)

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()

        train_loss          = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, mae, rmse = evaluate(model, val_loader, criterion, device)

        scheduler.step(val_loss)
        elapsed = time.time() - t0

        print(
            f"{epoch:>6}  {train_loss:>11.4f}  {val_loss:>10.4f}  "
            f"{mae:>7.4f}  {rmse:>7.4f}  {elapsed:>6.1f}s"
        )
        logger.info(
            "Epoch %d — train_loss=%.4f  val_loss=%.4f  MAE=%.4f  RMSE=%.4f",
            epoch, train_loss, val_loss, mae, rmse,
        )

        # ── Checkpoint & early stopping ───────────────────────────
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            no_improve    = 0
            ckpt_path     = CKPT_DIR / 'best_model.pt'
            torch.save(model.state_dict(), ckpt_path)
            logger.info("New best model saved → %s", ckpt_path)
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                logger.info(
                    "Early stopping triggered after %d epochs with no improvement.",
                    PATIENCE,
                )
                break

    print(f"\nTraining complete. Best validation loss: {best_val_loss:.4f}")
    print(f"Best model checkpoint: {CKPT_DIR / 'best_model.pt'}")


if __name__ == '__main__':
    main()
