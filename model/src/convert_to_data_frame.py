import os
import re
import json
import logging
from pathlib import Path
import pandas as pd

from data_loader import DataLoader

logger = logging.getLogger(__name__)


class ConvertToDataFrame(DataLoader):
    """
    Converts collected JSON metadata and matched images into a single
    tidy pandas DataFrame for model training and analysis.
    """

    def __init__(self, dir_name: str | None = None) -> None:
        if dir_name is None:
            script_dir = Path(__file__).parent.resolve()
            root_dir = script_dir if (script_dir / 'config.yaml').exists() else script_dir.parent
            dir_name = str(root_dir / 'data')
        super().__init__(dir_name)

    def _flatten(self, items: list) -> list[float]:
        """Recursively flattens nested lists/tuples of numeric values."""
        flat: list[float] = []
        for x in items:
            if isinstance(x, (list, tuple)):
                flat.extend(self._flatten(x))
            elif x is not None:
                try:
                    flat.append(float(x))
                except (ValueError, TypeError):
                    pass
        return flat

    def _aggregate(self, values: list) -> dict:
        """
        Returns mean, min, and max for a list of numeric values,
        safely handling multi-dimensional instrument arrays.
        """
        flat = self._flatten(values) if isinstance(values, list) else []
        if not flat:
            return {'mean': None, 'min': None, 'max': None}
        return {
            'mean': round(sum(flat) / len(flat), 4),
            'min': round(min(flat), 4),
            'max': round(max(flat), 4)
        }

    def _extract_sample_id(self, image_path: str) -> str:
        """Extracts unique sample/fruit identifier from image filename."""
        filename = Path(image_path.replace('\\', '/')).name
        match = re.match(r'^([a-zA-Z]+\d+)', filename)
        return match.group(1) if match else 'unknown'

    def create_data_frame(self) -> pd.DataFrame:
        all_data = []
        json_files = self.get_json_files()
        logger.info("Processing %d JSON files into DataFrame...", len(json_files))

        for file in json_files:
            try:
                with open(file, 'r') as f:
                    load_json = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Skipping unreadable JSON file %s: %s", file, e)
                continue

            day         = load_json.get('day_index')
            date        = load_json.get('date_started')
            images      = load_json.get('images', [])
            environment = load_json.get('environment')
            temperature = load_json.get('temperature')
            humidity    = load_json.get('humidity')
            light       = load_json.get('light_type')
            days_remaining = load_json.get('days_remaining')

            brix          = self._aggregate(load_json.get('brix', []))
            ph            = self._aggregate(load_json.get('ph', []))
            texture       = self._aggregate(load_json.get('texture', []))
            weight_loss   = self._aggregate(load_json.get('weight_loss', []))
            ripeness_index = self._aggregate(load_json.get('ripeness_index', []))

            for image in images:
                # Normalize slashes
                norm_image_path = image.replace('\\', '/')
                clean_rel = norm_image_path.lstrip('./')

                # Check if image file exists on disk
                candidates = [
                    self.data_dir.parent / clean_rel,
                    self.data_dir / clean_rel.replace('data/', '', 1),
                    Path(clean_rel),
                    Path(norm_image_path),
                ]
                if not any(cand.exists() for cand in candidates):
                    continue

                sample_id = self._extract_sample_id(norm_image_path)

                row = {
                    'Sample_ID':             sample_id,
                    'Day':                   day,
                    'Date':                  date,
                    'Image Path':            norm_image_path,
                    'days_remaining':        days_remaining,
                    'Environment':           environment,
                    'Temperature':           temperature,
                    'Humidity':              humidity,
                    'Light Type':            light,
                    'Brix Mean':             brix['mean'],
                    'Brix Min':              brix['min'],
                    'Brix Max':              brix['max'],
                    'pH Mean':               ph['mean'],
                    'pH Min':                ph['min'],
                    'pH Max':                ph['max'],
                    'Texture Mean':          texture['mean'],
                    'Texture Min':           texture['min'],
                    'Texture Max':           texture['max'],
                    'Weight Loss Mean':      weight_loss['mean'],
                    'Weight Loss Min':       weight_loss['min'],
                    'Weight Loss Max':       weight_loss['max'],
                    'Ripeness Index Mean':   ripeness_index['mean'],
                    'Ripeness Index Min':    ripeness_index['min'],
                    'Ripeness Index Max':    ripeness_index['max'],
                }
                all_data.append(row)

        dataframe = pd.DataFrame(all_data)
        logger.info("Successfully constructed DataFrame with %d rows.", len(dataframe))
        return dataframe


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    )
    script_dir = Path(__file__).parent.resolve()
    root_dir   = script_dir if (script_dir / 'config.yaml').exists() else script_dir.parent

    dataframe = ConvertToDataFrame().create_data_frame()
    csv_path = root_dir / 'preprocessed_data.csv'
    dataframe.to_csv(csv_path, index=False)
    print(f"Exported preprocessed data ({len(dataframe)} rows) to: {csv_path}")
