"""
predict.py
----------
Inference script for the Smart Shelf Life Prediction Model.

Usage:
    python src/predict.py --image path/to/mango.jpg --temp 25.0 --humidity 65.0 --env ambient
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path

import torch
from PIL import Image

# Ensure src is in the system path for imports
src_dir = Path(__file__).parent.resolve()
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

# Add root folder to search path as well to read config.yaml
root_dir = src_dir.parent.resolve()

from fusion_model import MultimodalShelfLifeModel
from image_backbone import get_eval_transforms

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Predict the remaining shelf life of a mango."
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the mango RGB image.",
    )
    parser.add_argument(
        "--temp",
        type=float,
        required=True,
        help="Ambient temperature reading in degrees Celsius.",
    )
    parser.add_argument(
        "--humidity",
        type=float,
        required=True,
        help="Relative humidity percentage.",
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=["ambient", "controlled"],
        required=True,
        help="Storage environment type ('ambient' or 'controlled').",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="checkpoints/best_model.pt",
        help="Path to the saved model checkpoint.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the project configuration YAML file.",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load configuration
    config_file = root_dir / args.config
    if not config_file.exists():
        logger.error("Configuration file '%s' not found.", config_file)
        sys.exit(1)

    config = load_config(config_file)
    img_cfg = config["image_model"]
    tab_cfg = config["tabular_model"]

    # Locate checkpoint
    ckpt_path = root_dir / args.checkpoint
    if not ckpt_path.exists():
        logger.error("Model checkpoint '%s' not found. Please train the model first.", ckpt_path)
        sys.exit(1)

    # Initialize model
    model = MultimodalShelfLifeModel(
        img_output_dim=img_cfg["output_dim"],
        tab_output_dim=tab_cfg["output_dim"],
        freeze_backbone=img_cfg["freeze_base"],
        unfreeze_last_blocks=img_cfg.get("unfreeze_last_blocks", True),  # Sync with training optimization
        dropout_fusion=0.0,  # No dropout at inference
    )

    # Print parameter information for verification
    logger.info(
        "Model parameters - Total: %s, Trainable: %s",
        f"{model.total_params():,}",
        f"{model.trainable_params():,}",
    )

    # Load checkpoint
    logger.info("Loading model weights from '%s'...", ckpt_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    model.to(device)
    model.eval()

    # Preprocess image
    image_path = Path(args.image)
    if not image_path.exists():
        logger.error("Image file '%s' not found.", image_path)
        sys.exit(1)

    logger.info("Preprocessing image '%s'...", image_path)
    transform = get_eval_transforms()
    try:
        img_pil = Image.open(image_path).convert("RGB")
        image_tensor = transform(img_pil).unsqueeze(0).to(device)
    except Exception as e:
        logger.error("Failed to load or preprocess image: %s", e)
        sys.exit(1)

    # Prepare tabular record
    tabular_record = [
        {
            "Temperature": args.temp,
            "Humidity": args.humidity,
            "Environment": args.env,
        }
    ]

    # Inference
    logger.info("Running inference...")
    with torch.no_grad():
        prediction = model(image_tensor, tabular_record)
        days_remaining = prediction.item()

    print("\n" + "=" * 40)
    print("  Smart Shelf Life Prediction Result")
    print("=" * 40)
    print(f"  Inputs:")
    print(f"    - Image      : {image_path.name}")
    print(f"    - Temp       : {args.temp}°C")
    print(f"    - Humidity   : {args.humidity}%")
    print(f"    - Environment: {args.env}")
    print(f"  --------------------------------------")
    print(f"  Estimated Remaining Shelf Life:")
    print(f"    >>> {days_remaining:.1f} day(s) <<<")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
