# Smart Shelf Life Prediction Model — Setup and Execution Guide

This document describes how to set up, train, and run predictions using the multimodal deep learning pipeline for mango shelf-life estimation.

---

## 1. Prerequisites

- **Python**: Version 3.10 to 3.14.
- **Hardware**: CPU is sufficient for testing (training takes ~45 seconds/epoch), but a CUDA-compatible GPU is recommended for faster training.

---

## 2. Directory Structure

```
Smart-Shelf-Life-Prediction-Model/
├── checkpoints/              # Directory for model weight checkpoints
│   └── best_model.pt         # Saved model parameters (best val loss)
├── data/                     # Source dataset directories (images & json metadata)
├── docs/                     # Documentation files
│   └── setup.md              # Setup and pipeline documentation (this file)
├── src/                      # Source code modules
│   ├── __init__.py
│   ├── convert_to_data_frame.py  # Script to compile JSON metadata into a CSV
│   ├── data_loader.py            # File discovery and dataset pairing utility
│   ├── fusion_model.py           # Combined Multimodal PyTorch model & dataset
│   ├── image_backbone.py         # EfficientNet-B0 feature projection model
│   ├── json_file.py              # Deprecated alias pointing to data_loader.py
│   ├── predict.py                # Command-line tool to execute model inference
│   ├── tabular_branch.py         # MLP branch for environment sensor embedding
│   └── train.py                  # Pipeline training, evaluation, and checkpointing
├── config.yaml               # Hyperparameters and biological validation thresholds
├── generate_dummy_data.py    # Script to generate realistic mock images and JSON files
└── requirements.txt          # Python packaging requirements
```

---

## 3. Environment Setup

To keep the development environment isolated, set up a virtual environment in the project root:

```bash
# 1. Create a virtual environment named `.venv`
python -m venv .venv

# 2. Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install requirements
pip install -r requirements.txt
```

---

## 4. Pipeline Execution Steps

### Step 1: Generate Mock Data (Optional / For Testing)
If you do not have actual mango images or metadata yet, generate the synthetic dataset (336 PNG images & 168 metadata files):
```bash
python generate_dummy_data.py
```

### Step 2: Compile the Dataset CSV
Preprocess the files in `data/` to compile them into a unified flat dataset file `preprocessed_data.csv`:
```bash
python src/convert_to_data_frame.py
```
This script scans all subdirectories, extracts tabular features (like temperature and humidity), matches images to their target remaining days, and writes out `preprocessed_data.csv` with the `days_remaining` target column.

### Step 3: Train the Multimodal Model
Run the training script to split the dataset, download pretrained weights, and execute the regression training loop:
```bash
python src/train.py
```
* The best model weight checkpoint will automatically be saved to `checkpoints/best_model.pt`.
* Early stopping is configured with a default patience of 10 epochs.

---

## 5. Model Inference (Making Predictions)

To estimate the remaining shelf life of a new mango, run the prediction CLI by providing a photo and ambient environment sensor readings:

```bash
python src/predict.py \
  --image path/to/mango.jpg \
  --temp 26.5 \
  --humidity 72.0 \
  --env ambient
```

### CLI Arguments:
* `--image`: (Required) Path to the mango RGB image.
* `--temp`: (Required) Ambient temperature in °C.
* `--humidity`: (Required) Relative humidity percentage.
* `--env`: (Required) Environment type (`ambient` or `controlled`).
* `--checkpoint`: Path to the weights file (default: `checkpoints/best_model.pt`).
* `--config`: Path to the configuration file (default: `config.yaml`).

---

## 6. Model Architecture & Data Schema

### Architecture Fusing Visual and Tabular Data:
```
Image (RGB 224x224) ────► EfficientNet-B0 (Frozen) ───► Projection ───► 256-dim embedding ───┐
                                                                                           ├───► Concatenate (320-dim) ───► Regression Head ───► days_remaining
[Temp, Humidity, Env] ──► Tabular Feature Encoder ─────► Tabular MLP ──► 64-dim embedding ────┘
```

### Tabular Input Fields:
1. **Temperature** (`float`): Ambient temperature of the storage space in °C.
2. **Humidity** (`float`): Ambient relative humidity percentage.
3. **Environment** (`str`): `"ambient"` (room storage) or `"controlled"` (refrigeration/cold storage).

### Ground-Truth Biochemical Indicators (Ripening Trends):
During research data collection, the following destructive ground-truth indicators are tracked:
*   **TSS / Brix** (`float`): Soluble solids increase from **`8.5° to 16.5° Brix`** as starches turn to sugars.
*   **pH** (`float`): Increases from **`3.4` to `5.2`** as organic acids degrade (acidity decreases).
*   **Firmness / Texture** (`float`): Penetrometer force drops from **`80 N`** (hard) to **`8 N`** (soft).
*   **Physiological Weight Loss** (`float`): Increases up to **`18%`** under ambient storage, and **`8%`** under refrigeration (controlled).
*   **Ripeness Index** (`float`): Progresses from **`1.0` (unripe green)** to **`5.0` (fully ripe yellow/orange)**.

### Scientific Data Sources & References:
1. **National Mango Board**: *Mango Quality Assessment Guidelines* (standards for Brix, ripeness stages, and firmness testing via penetrometer).
2. **Rooban et al. (2026)**: *Physiochemical changes during different stages of fruit ripening of climacteric fruit of mango (Mangifera indica L.)*.
3. **Kishore et al. (2017)**: *Physico-chemical changes during progressive ripening of mango (Mangifera indica L.) under different temperature regimes*.

*Note: Destructive parameters are used **only** during data collection to construct ground-truth remaining days labels. Deployed models do not require these parameters at inference time.*
