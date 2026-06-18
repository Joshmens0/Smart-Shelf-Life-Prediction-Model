"""
generate_dummy_data.py
----------------------
Generates realistic dummy images and JSON metadata for the Smart Shelf Life
Prediction Model.

Creates data for:
  - 2 environments: ambient, controlled
  - 2 protocols: destructive, non-destructive
  - 14 days per combination
  - Multiple samples per day (3 JSON files per day-folder)
  - 2 dummy mango images per sample (referenced in the non-destructive folder)

Total generated:
  - 4 combos × 14 days × 3 samples = 168 JSON metadata files
  - 4 combos × 14 days × 3 samples × 2 images = 336 PNG images
"""

import json
import os
import random
import struct
import zlib
from pathlib import Path
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent / "data" / "mango"
ENVIRONMENTS = {
    "ambient-environment": {
        "env_label": "ambient",
        "max_shelf_life": 7,
        "temp_range": (24.0, 32.0),
        "humidity_range": (55.0, 75.0),
        "light_types": ["fluorescent", "natural", "LED"],
    },
    "controlled-environment": {
        "env_label": "controlled",
        "max_shelf_life": 21,
        "temp_range": (4.0, 12.0),
        "humidity_range": (85.0, 95.0),
        "light_types": ["none", "dim-LED"],
    },
}
PROTOCOLS = ["destructive", "non-destructive"]
NUM_DAYS = 14
SAMPLES_PER_DAY = 3       # Number of JSON files per day folder
IMAGES_PER_SAMPLE = 2     # Number of images per sample

# Naming convention prefixes:
#   ambient  destructive     → "aad"
#   ambient  non-destructive → "aand"
#   controlled destructive     → "cbd"  (matches existing cbd1.json)
#   controlled non-destructive → "cbnd"
PREFIX_MAP = {
    ("ambient-environment", "destructive"):      "aad",
    ("ambient-environment", "non-destructive"):  "aand",
    ("controlled-environment", "destructive"):   "cbd",
    ("controlled-environment", "non-destructive"): "cbnd",
}

DATE_START = datetime(2026, 5, 17)

# ──────────────────────────────────────────────────────────────────────
# Minimal PNG generator (no Pillow / numpy needed)
# ──────────────────────────────────────────────────────────────────────

def _create_png_bytes(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """Create a minimal valid PNG file in memory (solid colour)."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)

    # Build raw image data: filter byte (0) + RGB pixels per row
    raw_row = b"\x00" + bytes([r, g, b]) * width
    raw_data = raw_row * height
    compressed = zlib.compress(raw_data)
    idat = _chunk(b"IDAT", compressed)
    iend = _chunk(b"IEND", b"")

    return header + ihdr + idat + iend


def generate_mango_image(day: int, max_days: int, width: int = 224, height: int = 224) -> bytes:
    """
    Generate a dummy mango image whose colour shifts from green (fresh)
    to yellow to brown (spoiled) as `day` increases.
    Adds some random pixel-level noise to prevent identical images.
    """
    progress = min(day / max_days, 1.0)  # 0 = fresh, 1 = fully spoiled

    if progress < 0.5:
        # Green → Yellow transition
        t = progress / 0.5
        r = int(60 + t * 195)       # 60 → 255
        g = int(180 + t * 55)       # 180 → 235
        b = int(30 - t * 20)        # 30 → 10
    else:
        # Yellow → Brown transition
        t = (progress - 0.5) / 0.5
        r = int(255 - t * 115)      # 255 → 140
        g = int(235 - t * 155)      # 235 → 80
        b = int(10 + t * 20)        # 10 → 30

    # Add slight random variation so each image is unique
    r = max(0, min(255, r + random.randint(-15, 15)))
    g = max(0, min(255, g + random.randint(-15, 15)))
    b = max(0, min(255, b + random.randint(-15, 15)))

    return _create_png_bytes(width, height, r, g, b)


# ──────────────────────────────────────────────────────────────────────
# Realistic measurement generators
# ──────────────────────────────────────────────────────────────────────

def _rand_measurements(base: float, spread: float, n: int = 3) -> list[float]:
    """Generate `n` realistic measurements around a base value."""
    return [round(base + random.uniform(-spread, spread), 2) for _ in range(n)]


def generate_measurements(day: int, env_key: str) -> dict:
    """
    Generate biologically plausible measurement values that change with time.
    
    References for ripening standards:
      1. National Mango Board (mango.org) - Brix and Firmness standards
      2. Rooban et al. (2026) - pH and Soluble Solids progression
      3. Kishore et al. (2017) - Weight loss and temperature effects
    
    As a mango ripens:
      - Brix (sugar) increases from ~8.5 to ~16.5
      - pH increases (acidity decreases) from ~3.4 to ~5.2
      - Texture (firmness) decreases from ~80 N to ~8 N
      - Weight loss increases to ~18% (ambient) or ~8% (controlled)
      - Ripeness index increases from 1.0 to 5.0
    """
    max_life = ENVIRONMENTS[env_key]["max_shelf_life"]
    progress = min(day / max_life, 1.0)

    brix_base      = 8.5 + progress * 8.0               # 8.5 → 16.5
    ph_base        = 3.4 + progress * 1.8               # 3.4 → 5.2 (acidity decreases)
    texture_base   = 80.0 - progress * 72.0             # 80 N → 8 N
    wl_base        = progress * (8.0 if env_key.startswith("controlled") else 18.0)
    ri_base        = 1.0 + progress * 4.0               # 1.0 → 5.0

    return {
        "brix":           _rand_measurements(brix_base,    0.8),
        "ph":             _rand_measurements(ph_base,      0.15),
        "texture":        _rand_measurements(texture_base, 2.0),
        "weight_loss":    _rand_measurements(wl_base,      0.6),
        "ripeness_index": _rand_measurements(ri_base,      0.3),
    }


# ──────────────────────────────────────────────────────────────────────
# Main generator
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    total_json = 0
    total_images = 0

    for env_key, env_cfg in ENVIRONMENTS.items():
        for protocol in PROTOCOLS:
            prefix = PREFIX_MAP[(env_key, protocol)]
            
            for day in range(1, NUM_DAYS + 1):
                day_dir = BASE_DIR / env_key / protocol / f"day-{day}"
                day_dir.mkdir(parents=True, exist_ok=True)

                # Corresponding non-destructive image directory
                # (images are always stored under non-destructive)
                img_dir = BASE_DIR / env_key / "non-destructive" / f"day-{day}"
                img_dir.mkdir(parents=True, exist_ok=True)

                for sample_idx in range(1, SAMPLES_PER_DAY + 1):
                    sample_id = f"{prefix}{sample_idx}"

                    # ── Generate images ──────────────────────────
                    image_paths = []
                    for img_idx in range(1, IMAGES_PER_SAMPLE + 1):
                        # Unique image name per prefix+sample+image+day
                        img_name = f"{prefix}{sample_idx}img{img_idx}d{day}.png"

                        img_full_path = img_dir / img_name
                        png_bytes = generate_mango_image(
                            day, env_cfg["max_shelf_life"]
                        )
                        img_full_path.write_bytes(png_bytes)
                        total_images += 1

                        # Relative path as stored in the JSON
                        rel_img = (
                            f".\\data\\mango\\{env_key}\\non-destructive"
                            f"\\day-{day}\\{img_name}"
                        )
                        image_paths.append(rel_img)

                    # ── Generate measurements ────────────────────
                    measurements = generate_measurements(day, env_key)

                    # ── Compute days_remaining ───────────────────
                    days_remaining = max(0, env_cfg["max_shelf_life"] - day)

                    # ── Build metadata dict ──────────────────────
                    date_taken = DATE_START + timedelta(days=day - 1)
                    metadata = {
                        "environment": env_cfg["env_label"],
                        "temperature": round(
                            random.uniform(*env_cfg["temp_range"]), 1
                        ),
                        "humidity": round(
                            random.uniform(*env_cfg["humidity_range"]), 1
                        ),
                        "light_type": random.choice(env_cfg["light_types"]),
                        "date_started": date_taken.strftime("%Y-%m-%d"),
                        "day_index": day,
                        "days_remaining": days_remaining,
                        **measurements,
                        "images": image_paths,
                    }

                    # ── Write JSON ───────────────────────────────
                    json_path = day_dir / f"{sample_id}.json"
                    with open(json_path, "w") as f:
                        json.dump(metadata, f, indent=2)
                    total_json += 1

    print(f"[OK] Generated {total_json} JSON metadata files")
    print(f"[OK] Generated {total_images} PNG images (224x224)")
    print(f"     Across {len(ENVIRONMENTS)} environments x {len(PROTOCOLS)} protocols x {NUM_DAYS} days x {SAMPLES_PER_DAY} samples")


if __name__ == "__main__":
    random.seed(42)
    main()
