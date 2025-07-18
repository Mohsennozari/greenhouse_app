import pandas as pd
import os
from config import DATA_FOLDER

def preprocess_data():
    raw_path = os.path.join(DATA_FOLDER, 'greenhouse_raw.csv')
    clean_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    
    if not os.path.exists(raw_path):
        print(f"خطا: فایل {raw_path} پیدا نشد.")
        return False
    
    try:
        df = pd.read_csv(raw_path, parse_dates=['datetime'])
        # حذف مقادیر غیرمنطقی
        df = df.dropna()
        df = df[df['temperature'].between(0, 50)]
        df = df[df['humidity'].between(0, 100)]
        # فیلتر نور: در ساعات شب (8 شب تا 6 صبح) نور باید نزدیک به صفر باشد
        df['is_night'] = df['datetime'].dt.hour.between(20, 23) | df['datetime'].dt.hour.between(0, 5)
        df.loc[df['is_night'] & (df['light'] > 100), 'light'] = 0  # تنظیم نور غیرعادی در شب به صفر
        df = df[df['light'] >= 100]  # فیلتر نور غیرعادی در روز
        df = df.drop(columns=['is_night'])
        df.to_csv(clean_path, index=False)
        print(f"✅ داده‌های تمیز در {clean_path} ذخیره شد.")
        return True
    except Exception as e:
        print(f"خطا در پیش‌پردازش: {str(e)}")
        return False

if __name__ == '__main__':
    preprocess_data()