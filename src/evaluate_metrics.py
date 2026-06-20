"""
evaluate_metrics.py
-------------------
Computes performance metrics (MAE, RMSE, R² Score) for the trained Student model
on the validation split of the preprocessed dataset.

Usage:
    python src/evaluate_metrics.py
"""

import logging
import math
from pathlib import Path
import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader

from fusion_model import MultimodalDataset, MultimodalShelfLifeModel, collate_multimodal
from image_backbone import get_eval_transforms

logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).parent.absolute()
_ROOT_DIR   = _SCRIPT_DIR if (_SCRIPT_DIR / 'config.yaml').exists() else _SCRIPT_DIR.parent

CONFIG_PATH = _ROOT_DIR / 'config.yaml'
DATA_CSV    = _ROOT_DIR / 'preprocessed_data.csv'
CKPT_PATH   = _ROOT_DIR / 'checkpoints/best_model.pt'


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def compute_mae(preds: torch.Tensor, targets: torch.Tensor) -> float:
    return (preds - targets).abs().mean().item()


def compute_rmse(preds: torch.Tensor, targets: torch.Tensor) -> float:
    return math.sqrt(((preds - targets) ** 2).mean().item())


def compute_r2(preds: torch.Tensor, targets: torch.Tensor) -> float:
    """Calculates Coefficient of Determination (R²) score."""
    ss_res = ((targets - preds) ** 2).sum().item()
    ss_tot = ((targets - targets.mean()) ** 2).sum().item()
    if ss_tot == 0:
        return 0.0
    return 1.0 - (ss_res / ss_tot)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = load_config()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info("Using device: %s", device)

    # Load dataset
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"'{DATA_CSV}' not found. Run preprocessing first.")
    df = pd.read_csv(DATA_CSV)

    # Perform validation split matching train.py
    val_size   = max(1, int(0.2 * len(df)))
    train_size = len(df) - val_size
    val_df   = df.iloc[train_size:].reset_index(drop=True)
    logger.info("Loaded %d validation records.", len(val_df))

    # Datasets & loaders
    val_dataset = MultimodalDataset(val_df, transform=get_eval_transforms())
    val_loader = DataLoader(
        val_dataset,
        batch_size=8,
        shuffle=False,
        collate_fn=collate_multimodal,
        num_workers=0,
    )

    # Instantiate Student Model
    img_cfg = config['image_model']
    tab_cfg = config['tabular_model']

    model = MultimodalShelfLifeModel(
        img_output_dim=img_cfg['output_dim'],
        tab_output_dim=tab_cfg['output_dim'],
        freeze_backbone=img_cfg['freeze_base'],
        dropout_fusion=0.0,  # No dropout for evaluation
    ).to(device)

    # Load Checkpoint
    if not CKPT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint '{CKPT_PATH}' not found. Train the model first.")
    logger.info("Loading Student model weights from '%s'...", CKPT_PATH)
    model.load_state_dict(torch.load(CKPT_PATH, map_location=device))
    model.eval()

    # Evaluate
    all_preds = []
    all_targets = []

    logger.info("Running performance evaluation...")
    with torch.no_grad():
        for images, tabulars, labels, _ in val_loader:
            images = images.to(device)
            preds = model(images, tabulars)
            
            all_preds.append(preds.cpu())
            all_targets.append(labels.cpu())

    all_preds = torch.cat(all_preds)
    all_targets = torch.cat(all_targets)

    # Calculate metrics
    mae = compute_mae(all_preds, all_targets)
    rmse = compute_rmse(all_preds, all_targets)
    r2 = compute_r2(all_preds, all_targets)

    print("\n" + "=" * 45)
    print("  Student Model Validation Performance")
    print("=" * 45)
    print(f"  Dataset Size  : {len(all_targets)} samples")
    print(f"  -------------------------------------------")
    print(f"  Mean Absolute Error (MAE)  : {mae:.4f} day(s)")
    print(f"  Root Mean Sq. Error (RMSE) : {rmse:.4f} day(s)")
    print(f"  R² Coefficient (R-squared) : {r2:.4f}")
    print("=" * 45 + "\n")


if __name__ == '__main__':
    main()
