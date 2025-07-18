import pandas as pd
import os
from config import DATA_FOLDER

def preprocess_data(input_file='data/greenhouse_raw.csv', output_file='data/greenhouse_clean.csv'):
    input_path = os.path.join(DATA_FOLDER, input_file)
    output_path = os.path.join(DATA_FOLDER, output_file)
    
    if not os.path.exists(input_path):
        print(f"خطا: فایل {input_path} پیدا نشد.")
        return False
    
    # بررسی ستون‌های مورد نیاز
    df = pd.read_csv(input_path, nrows=1)
    required_columns = ['datetime', 'temperature', 'humidity', 'light']
    if not all(col in df.columns for col in required_columns):
        print(f"خطا: فایل باید شامل ستون‌های {required_columns} باشد.")
        return False
    
    # پردازش داده‌ها با چانک برای بهینه‌سازی
    chunks = pd.read_csv(input_path, chunksize=10000, usecols=required_columns)
    df = pd.concat([chunk for chunk in chunks])
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df.dropna(subset=['datetime', 'temperature', 'humidity', 'light'], inplace=True)
    
    # بررسی مقادیر غیرعادی نور
    if df['light'].mean() < 100:
        print("هشدار: مقادیر نور بسیار پایین است، احتمال خطای سنسور.")
    
    df = df.sort_values(by='datetime')
    df.to_csv(output_path, index=False)
    print(f"✅ فایل تمیز شده ذخیره شد: {output_path}")
    return True

if __name__ == '__main__':
    preprocess_data()