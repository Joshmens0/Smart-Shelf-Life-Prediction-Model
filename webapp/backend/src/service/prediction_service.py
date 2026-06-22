# ruff: noqa: E402
import sys
import torch
import yaml
from pathlib import Path
from PIL import Image

# Setup model search path references
core_dir = Path(__file__).resolve().parent
backend_src_dir = core_dir.parent
repo_root = backend_src_dir.parents[2]
model_src = repo_root / "model" / "src"

if str(model_src) not in sys.path:
    sys.path.append(str(model_src))

from fusion_model import MultimodalShelfLifeModel
from image_backbone import get_eval_transforms
from core.config import settings

class PredictionService:
    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        config_path = repo_root / settings.MODEL_CONFIG_PATH
        checkpoint_path = repo_root / settings.MODEL_CHECKPOINT_PATH
        
        if not config_path.exists():
            raise FileNotFoundError(f"Model config file not found at: {config_path}")
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Model weights checkpoint not found at: {checkpoint_path}")
            
        self.config = self._load_yaml(config_path)
        self.model = self._load_model(checkpoint_path)
        self.transform = get_eval_transforms()

    def _load_yaml(self, path: Path) -> dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_model(self, checkpoint_path: Path) -> MultimodalShelfLifeModel:
        img_cfg = self.config["image_model"]
        tab_cfg = self.config["tabular_model"]
        
        model = MultimodalShelfLifeModel(
            img_output_dim=img_cfg["output_dim"],
            tab_output_dim=tab_cfg["output_dim"],
            freeze_backbone=img_cfg["freeze_base"],
            unfreeze_last_blocks=img_cfg.get("unfreeze_last_blocks", True),
            dropout_fusion=0.0
        )
        
        state_dict = torch.load(checkpoint_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        return model

    def predict(self, img_path: Path, temp: float, humidity: float, env: str) -> float:
        """Runs the multimodal inference pipeline for the given image and sensor attributes."""
        if not img_path.exists():
            raise FileNotFoundError(f"Source image not found: {img_path}")
            
        # 1. Preprocess the image
        img_pil = Image.open(img_path).convert("RGB")
        image_tensor = self.transform(img_pil).unsqueeze(0).to(self.device)

        # 2. Build tabular dataset dictionary input
        tabular_record = [{
            "Temperature": temp,
            "Humidity": humidity,
            "Environment": env
        }]

        # 3. Model execution
        with torch.no_grad():
            prediction = self.model(image_tensor, tabular_record)
            days_remaining = float(prediction.item())
            
        # Shelf life cannot be negative (floor at 0.0)
        return max(0.0, days_remaining)

# Global singleton
prediction_service_instance = None

def get_prediction_service() -> PredictionService:
    global prediction_service_instance
    if prediction_service_instance is None:
        prediction_service_instance = PredictionService()
    return prediction_service_instance
