import os
import json

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# تنظیمات پیش‌فرض
DEFAULT_THRESHOLDS = {
    'temperature': {'min': 15, 'max': 30},
    'humidity': {'min': 60, 'max': 90},
    'light': {'min': 1000, 'max': 20000}
}

# بارگذاری یا ایجاد فایل تنظیمات
def load_thresholds():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"خطا در بارگذاری تنظیمات: {str(e)}")
            return DEFAULT_THRESHOLDS
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_THRESHOLDS, f, ensure_ascii=False, indent=4)
        return DEFAULT_THRESHOLDS

# ذخیره تنظیمات
def save_thresholds(thresholds):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(thresholds, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"خطا در ذخیره تنظیمات: {str(e)}")
        return False

THRESHOLDS = load_thresholds()