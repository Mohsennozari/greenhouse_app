import pandas as pd
import os
from config import DATA_FOLDER, THRESHOLDS

def preprocess_data():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    raw_path = os.path.join(DATA_FOLDER, 'greenhouse_raw.csv')
    clean_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    
    if not os.path.exists(raw_path):
        print(f"خطا: فایل {raw_path} پیدا نشد.")
        return False
    
    try:
        df = pd.read_csv(raw_path, parse_dates=['datetime'])
        # حذف مقادیر نامعتبر
        df = df.dropna()
        df = df[df['temperature'].between(THRESHOLDS['temperature']['min'] - 10, THRESHOLDS['temperature']['max'] + 10)]
        df = df[df['humidity'].between(0, 100)]
        df = df[df['light'] >= 0]

        # معکوس کردن مقادیر نور برای روز و شب
        df['hour'] = df['datetime'].dt.hour
        day_mask = (df['hour'] >= 6) & (df['hour'] < 18)
        night_mask = (df['hour'] < 6) | (df['hour'] >= 18)
        # فرض: نور روز باید کمتر باشد (مثلاً تا 5000 لوکس) و نور شب بیشتر (مثلاً بالای 5000 لوکس)
        df.loc[day_mask, 'light'], df.loc[night_mask, 'light'] = df.loc[night_mask, 'light'].values, df.loc[day_mask, 'light'].values
        df = df.drop(columns=['hour'])

        # ذخیره داده‌های تمیز
        df.to_csv(clean_path, index=False)
        print(f"داده‌های تمیز در {clean_path} ذخیره شد.")
        return True
    except Exception as e:
        print(f"خطا در پیش‌پردازش داده‌ها: {str(e)}")
        return False