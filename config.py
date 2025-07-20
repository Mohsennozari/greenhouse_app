import os
import json

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')

THRESHOLDS = {
    'temperature': {'min': 15.0, 'max': 30.0},
    'humidity': {'min': 40.0, 'max': 80.0},
    'light': {'min': 5000, 'max': 50000}
}

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_thresholds = json.load(f)
            THRESHOLDS.update(loaded_thresholds)
    except Exception as e:
        print(f"خطا در بارگذاری config.json: {str(e)}")

def save_thresholds(thresholds):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(thresholds, f, indent=4)
        return True
    except Exception as e:
        print(f"خطا در ذخیره آستانه‌ها: {str(e)}")
        return False