import pandas as pd
import os
from config import DATA_FOLDER

def preprocess_data():
    raw_path = os.path.join(DATA_FOLDER, 'greenhouse_raw.csv')
    clean_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    try:
        df = pd.read_csv(raw_path)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.dropna(subset=['temperature', 'humidity', 'light'])
        df = df[df['temperature'].between(-50, 100)]
        df = df[df['humidity'].between(0, 100)]
        df = df[df['light'].between(0, 100000)]
        night_hours = df['datetime'].dt.hour.between(20, 23) | df['datetime'].dt.hour.between(0, 5)
        df.loc[night_hours & (df['light'] > 100), 'light'] = 0  # تنظیم نور غیرعادی در شب به صفر
        df.to_csv(clean_path, index=False)
        return True
    except Exception as e:
        print(f"خطا در پیش‌پردازش: {str(e)}")
        return False