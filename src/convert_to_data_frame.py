import pandas as pd
import json
from pathlib import Path
from data_loader import DataLoader


class ConvertToDataFrame(DataLoader):
    def __init__(self, dir_name: str | None = None) -> None:
        if dir_name is None:
            script_dir = Path(__file__).parent.absolute()
            root_dir   = script_dir if (script_dir / 'config.yaml').exists() else script_dir.parent
            dir_name   = str(root_dir / 'data')
        super().__init__(dir_name)
    def _aggregate(self, values: list) -> dict:
        """Returns mean, min, and max for a list of numeric values."""
        if not values:
            return {'mean': None, 'min': None, 'max': None}
        return {
            'mean': round(sum(values) / len(values), 4),
            'min': min(values),
            'max': max(values)
        }

    def create_data_frame(self) -> pd.DataFrame:
        all_data = []
        for file in self.get_json_files():
            print(file)
            with open(file, 'r') as f:
                load_json = json.load(f)

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
                row = {
                    'Day':                   day,
                    'Date':                  date,
                    'Image Path':            image,
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
        return dataframe
        
if __name__== "__main__":
    script_dir = Path(__file__).parent.absolute()
    root_dir   = script_dir if (script_dir / 'config.yaml').exists() else script_dir.parent
    
    dataframe = ConvertToDataFrame().create_data_frame()
    csv_path = root_dir / 'preprocessed_data.csv'
    dataframe.to_csv(csv_path, index=False)
    print(f"Exported preprocessed data ({len(dataframe)} rows) to: {csv_path}")
    
