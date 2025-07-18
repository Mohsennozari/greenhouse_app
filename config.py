import os
import json

# مسیر پوشه داده‌ها
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')

# آستانه‌های پیش‌فرض
THRESHOLDS = {
    'temperature': {'min': 15.0, 'max': 30.0},
    'humidity': {'min': 40.0, 'max': 80.0},
    'light': {'min': 5000, 'max': 50000}
}

# بارگذاری آستانه‌ها از config.json اگر وجود داشته باشد
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            THRESHOLDS = json.load(f)
    except Exception as e:
        print(f"خطا در بارگذاری config.json: {str(e)}")

def save_thresholds(thresholds):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(thresholds, f, indent=4)
        return True
    except Exception as e:
        print(f"خطا در ذخیره آستانه‌ها: {str(e)}")
        return False