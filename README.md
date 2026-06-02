# Smart Shelf Life Prediction Model 🥭

A multimodal machine learning pipeline for predicting the remaining shelf life of mangoes.
The model fuses **RGB image data** with **environmental sensor readings** (temperature and humidity)
to regress the number of days before spoilage — enabling non-destructive freshness assessment
in the field, store, or cold chain.

---

## Project Overview

### The Problem
Determining mango shelf life traditionally requires **destructive laboratory tests** (measuring
sugar content, pH, firmness, etc.), which are time-consuming, costly, and sacrifice the fruit.

### The Solution
This project trains a multimodal deep learning model on a controlled dataset — pairing images
with destructive ground-truth measurements — so that the deployed model can predict shelf life
from a **photo + two sensor readings alone**.

### Inference-Time Inputs (what the end user provides)
| Input | Type | Source |
|---|---|---|
| Mango image | Photo (224×224 RGB) | Camera / smartphone |
| Temperature | Float (°C) | Thermometer / IoT sensor |
| Humidity | Float (%) | Humidity sensor |
| Storage type | `ambient` or `controlled` | User-selected |

> **Note**: Destructive measurements (Brix, pH, texture, weight loss, ripeness index) are
> used **only during data collection** to produce accurate `days_remaining` labels.
> They are **not required at inference time**.

---

## Model Architecture

```
Image (3×224×224) ──► EfficientNet-B0 ──► 256-dim embedding ──┐
                       (pretrained, frozen)                     │
                                                               cat(320) ──► Fusion Head ──► days_remaining
[Temperature, Humidity,               ──► MLP ──► 64-dim  ────┘
 Environment]                            (3-layer)
```

### Components

| Module | File | Description |
|---|---|---|
| **Image Backbone** | `src/image_backbone.py` | EfficientNet-B0 pretrained on ImageNet. Frozen conv layers + trainable projection head → 256-dim |
| **Tabular Branch** | `src/tabular_branch.py` | Categorical embedding for Environment + numerical passthrough for Temp/Humidity → MLP → 64-dim |
| **Fusion Model** | `src/fusion_model.py` | Concatenates both embeddings (320-dim) → 3-layer regression head → `days_remaining` |

### Parameter Budget
| | Count |
|---|---|
| Total parameters | 4,423,689 |
| Trainable (heads only) | 416,141 |
| Frozen (EfficientNet backbone) | 4,007,548 |

---

## Directory Structure

```
Smart Shelf Life Prediction Model/
├── config.yaml                   # Project-wide configuration & hyperparameters
├── requirements.txt              # Python dependencies
├── README.md
├── preprocessed_data.csv         # Output of convert_to_data_frame.py
│
├── data/
│   └── mango/
│       ├── ambient-environment/
│       │   ├── destructive/
│       │   │   └── day-N/        # JSON metadata files (aadN.json)
│       │   └── non-destructive/
│       │       └── day-N/        # Image files (.png/.jpg)
│       └── controlled-environment/
│           ├── destructive/
│           └── non-destructive/
│
├── checkpoints/
│   └── best_model.pt             # Saved after best validation epoch
│
└── src/
    ├── __init__.py
    ├── data_loader.py            # File discovery, image-metadata matching, JSON updater
    ├── json_file.py              # Deprecated alias → DataLoader
    ├── convert_to_data_frame.py  # Builds preprocessed_data.csv from JSON files
    ├── image_backbone.py         # EfficientNet-B0 feature extractor + MangoImageDataset
    ├── tabular_branch.py         # Sensor feature encoder + MLP branch
    ├── fusion_model.py           # Full MultimodalShelfLifeModel + MultimodalDataset
    └── train.py                  # Training loop, checkpointing, early stopping
```

---

## Data Schema

Each `dayN.json` metadata file contains:

| Field | Type | Description | Used As |
|---|---|---|---|
| `environment` | `str` | `"ambient"` or `"controlled"` | Model input |
| `temperature` | `float` | Ambient temperature (°C) | Model input |
| `humidity` | `float` | Relative humidity (%) | Model input |
| `light_type` | `str` | Type of lighting | Reference only |
| `date_started` | `str` | Experiment start date (ISO 8601) | Reference only |
| `day_index` | `int` | Day number in the experiment | Reference only |
| `days_remaining` | `int` | **Regression target** — days before spoilage | **Label** |
| `brix` | `[float]` | Sugar content readings (°Brix) | Label derivation |
| `ph` | `[float]` | pH measurements | Label derivation |
| `texture` | `[float]` | Firmness readings (N) | Label derivation |
| `weight_loss` | `[float]` | Weight loss (%) | Label derivation |
| `ripeness_index` | `[float]` | Calculated ripeness index | Label derivation |
| `images` | `[str]` | Paths to linked non-destructive images | Model input |

---

## Setup

```bash
# Clone / open the project
cd "Smart Shelf Life Prediction Model"

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies (use the same Python as the venv)
pip install -r requirements.txt
```

---

## Usage

### Step 1 — Preprocess the data
Walks the `data/` directory, links images to their JSON metadata, and exports a flat CSV:
```bash
python src/convert_to_data_frame.py
```

### Step 2 — Train the model
```bash
python src/train.py
```
Outputs per-epoch **MAE** and **RMSE** (both in days). Best checkpoint is saved to
`checkpoints/best_model.pt` with early stopping (patience = 10 epochs).

### Step 3 — Inference (example)
```python
import torch
from PIL import Image
from src.fusion_model import MultimodalShelfLifeModel
from src.image_backbone import get_eval_transforms

model = MultimodalShelfLifeModel()
model.load_state_dict(torch.load('checkpoints/best_model.pt'))
model.eval()

image   = get_eval_transforms()(Image.open('mango.jpg').convert('RGB')).unsqueeze(0)
tabular = [{'Temperature': 26.0, 'Humidity': 70.0, 'Environment': 'ambient'}]

with torch.no_grad():
    days = model(image, tabular).item()

print(f"Estimated shelf life: {days:.1f} day(s)")
```

---

## Training Details

| Setting | Value |
|---|---|
| Loss | MSE |
| Optimiser | Adam (lr=1e-3, weight_decay=1e-4) |
| Scheduler | ReduceLROnPlateau (factor=0.5, patience=5) |
| Early stopping | patience=10 epochs |
| Batch size | 8 |
| Train / Val split | 80 / 20 |
| Backbone | EfficientNet-B0 (frozen) |
| Metrics reported | MAE (days), RMSE (days) |

---

## Status

> 🚧 **Under active development** — data collection and pipeline stage.

| Stage | Status |
|---|---|
| Data pipeline (loading, linking, CSV export) | ✅ Complete |
| Image backbone (EfficientNet-B0) | ✅ Complete |
| Tabular branch (sensor MLP) | ✅ Complete |
| Fusion model | ✅ Complete |
| Training loop + checkpointing | ✅ Complete |
| Dataset collection (filling JSON files) | 🔄 In progress |
| Model training & evaluation | ⏳ Pending data |
| Inference API / deployment | ⏳ Planned |
