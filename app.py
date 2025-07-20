from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_caching import Cache
from dotenv import load_dotenv
import pandas as pd
import os
from datetime import datetime
import jdatetime
from config import DATA_FOLDER, THRESHOLDS, save_thresholds
from report_generator import generate_report

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("کلید مخفی Flask تنظیم نشده است.")

app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

def check_thresholds(df):
    alerts = {'temperature': False, 'humidity': False, 'light': False}
    if not df.empty:
        latest = df.iloc[-1]
        for metric in alerts:
            if pd.notna(latest[metric]) and (latest[metric] < THRESHOLDS[metric]['min'] or latest[metric] > THRESHOLDS[metric]['max']):
                alerts[metric] = True
    return alerts

def calculate_confidence_and_distance(df):
    if df.empty:
        return {
            'temperature': 0.0,
            'humidity': 0.0,
            'light': 0.0,
            'temp_distance': 0.0,
            'hum_distance': 0.0,
            'light_distance': 0.0,
            'temp_confidence': 0.0,
            'hum_confidence': 0.0,
            'light_confidence': 0.0,
            'temperature_alert': False,
            'humidity_alert': False,
            'light_alert': False
        }
    
    latest = df.iloc[-1]
    result = {
        'temperature': float(latest['temperature']) if pd.notna(latest['temperature']) else 0.0,
        'humidity': float(latest['humidity']) if pd.notna(latest['humidity']) else 0.0,
        'light': float(latest['light']) if pd.notna(latest['light']) else 0.0
    }
    for metric in ['temperature', 'humidity', 'light']:
        value = result[metric]
        min_val = THRESHOLDS[metric]['min']
        max_val = THRESHOLDS[metric]['max']
        # محاسبه فاصله از نزدیک‌ترین آستانه
        distance = min(abs(value - min_val), abs(value - max_val)) if value != 0.0 else 0.0
        # محاسبه درصد اطمینان
        optimal = (min_val + max_val) / 2
        max_distance = max(abs(optimal - min_val), abs(optimal - max_val))
        confidence = 100 * (1 - abs(value - optimal) / max_distance) if max_distance > 0 and value != 0.0 else 0.0
        alert = value < min_val or value > max_val
        result[f'{metric[:4]}_distance'] = float(distance)
        result[f'{metric[:4]}_confidence'] = float(max(0, min(100, confidence)))
        result[f'{metric}_alert'] = alert
    return result

def analyze_sensor_performance(df):
    performance = {}
    for metric in ['temperature', 'humidity', 'light']:
        total_count = len(df)
        valid_count = len(df[df[metric].notna()])
        outliers = len(df[(df[metric] < THRESHOLDS[metric]['min']) | (df[metric] > THRESHOLDS[metric]['max'])])
        error_rate = ((total_count - valid_count) / total_count * 100) if total_count > 0 else 0.0
        performance[metric] = {
            'valid_count': valid_count,
            'outliers': outliers,
            'error_rate': float(error_rate)
        }
    return performance

def calculate_light_stats(df):
    df['hour'] = df['datetime'].dt.hour
    # معکوس کردن داده‌های نور برای روز و شب
    day_df = df[(df['hour'] >= 6) & (df['hour'] < 18)]
    night_df = df[(df['hour'] < 6) | (df['hour'] >= 18)]
    
    light_day_stats = {
        'mean': float(night_df['light'].mean()) if not night_df.empty else 0.0,
        'min': float(night_df['light'].min()) if not night_df.empty else 0.0,
        'max': float(night_df['light'].max()) if not night_df.empty else 0.0,
        'median': float(night_df['light'].median()) if not night_df.empty else 0.0,
        'std': float(night_df['light'].std()) if not night_df.empty else 0.0,
        'count': len(night_df),
        'range': float(night_df['light'].max() - night_df['light'].min()) if not night_df.empty else 0.0,
        'outliers': len(night_df[(night_df['light'] < THRESHOLDS['light']['min']) | (night_df['light'] > THRESHOLDS['light']['max'])]) if not night_df.empty else 0
    }
    light_night_stats = {
        'mean': float(day_df['light'].mean()) if not day_df.empty else 0.0,
        'min': float(day_df['light'].min()) if not day_df.empty else 0.0,
        'max': float(day_df['light'].max()) if not day_df.empty else 0.0,
        'median': float(day_df['light'].median()) if not day_df.empty else 0.0,
        'std': float(day_df['light'].std()) if not day_df.empty else 0.0,
        'count': len(day_df),
        'range': float(day_df['light'].max() - day_df['light'].min()) if not day_df.empty else 0.0,
        'outliers': len(day_df[(day_df['light'] < THRESHOLDS['light']['min']) | (day_df['light'] > THRESHOLDS['light']['max'])]) if not day_df.empty else 0
    }
    return light_day_stats, light_night_stats

@app.route('/')
@cache.cached(timeout=3600, query_string=True)
def index():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    table_start_date = request.args.get('table_start_date', '')
    table_end_date = request.args.get('table_end_date', '')
    temp_min_filter = request.args.get('temp_min_filter', '')
    temp_max_filter = request.args.get('temp_max_filter', '')
    hum_min_filter = request.args.get('hum_min_filter', '')
    hum_max_filter = request.args.get('hum_max_filter', '')
    light_min_filter = request.args.get('light_min_filter', '')
    light_max_filter = request.args.get('light_max_filter', '')
    date_format = request.args.get('date_format', 'gregorian')

    data_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    table_rows = []
    stats = None
    alerts = {'temperature': False, 'humidity': False, 'light': False}
    latest_data = None
    sensor_performance = None

    if os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path, parse_dates=['datetime']).tail(1000)
            df_original = df.copy()
            if date_format == 'jalali':
                df['datetime'] = df['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M:%S'))

            # فیلتر جدول
            if table_start_date and table_end_date:
                try:
                    if date_format == 'jalali':
                        start_dt = jdatetime.datetime.strptime(table_start_date, '%Y/%m/%d').togregorian()
                        end_dt = jdatetime.datetime.strptime(table_end_date, '%Y/%m/%d').togregorian()
                    else:
                        start_dt = datetime.strptime(table_start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(table_end_date, '%Y-%m-%d')
                    df = df[(df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)]
                except ValueError as e:
                    flash(f'خطا در فرمت تاریخ جدول: لطفاً تاریخ را به فرمت {"YYYY/MM/DD" if date_format == "jalali" else "YYYY-MM-DD"} وارد کنید.')

            if temp_min_filter:
                df = df[df['temperature'] >= float(temp_min_filter)]
            if temp_max_filter:
                df = df[df['temperature'] <= float(temp_max_filter)]
            if hum_min_filter:
                df = df[df['humidity'] >= float(hum_min_filter)]
            if hum_max_filter:
                df = df[df['humidity'] <= float(hum_max_filter)]
            if light_min_filter:
                df = df[df['light'] >= float(light_min_filter)]
            if light_max_filter:
                df = df[df['light'] <= float(light_max_filter)]

            # فیلتر نمودارها و تحلیل‌ها
            if start_date and end_date:
                try:
                    if date_format == 'jalali':
                        start_date_dt = jdatetime.datetime.strptime(start_date, '%Y/%m/%d').togregorian().strftime('%Y-%m-%d')
                        end_date_dt = jdatetime.datetime.strptime(end_date, '%Y/%m/%d').togregorian().strftime('%Y-%m-%d')
                    else:
                        start_date_dt = start_date
                        end_date_dt = end_date
                    df_original = df_original[(df_original['datetime'] >= start_date_dt) & (df_original['datetime'] <= end_date_dt)]
                    filtered_data_path = 'filtered_data.csv'
                    df_original.to_csv(os.path.join(DATA_FOLDER, filtered_data_path), index=False)
                    generate_report(data_path=filtered_data_path, date_format=date_format)
                except ValueError as e:
                    flash(f'خطا در فرمت تاریخ: لطفاً تاریخ را به فرمت {"YYYY/MM/DD" if date_format == "jalali" else "YYYY-MM-DD"} وارد کنید.')

            stats = {
                'temperature': {
                    'mean': float(df_original['temperature'].mean()) if not df_original.empty else 0.0,
                    'min': float(df_original['temperature'].min()) if not df_original.empty else 0.0,
                    'max': float(df_original['temperature'].max()) if not df_original.empty else 0.0,
                    'median': float(df_original['temperature'].median()) if not df_original.empty else 0.0,
                    'std': float(df_original['temperature'].std()) if not df_original.empty else 0.0,
                    'count': len(df_original['temperature']),
                    'range': float(df_original['temperature'].max() - df_original['temperature'].min()) if not df_original.empty else 0.0,
                    'outliers': len(df_original[(df_original['temperature'] < THRESHOLDS['temperature']['min']) | (df_original['temperature'] > THRESHOLDS['temperature']['max'])])
                },
                'humidity': {
                    'mean': float(df_original['humidity'].mean()) if not df_original.empty else 0.0,
                    'min': float(df_original['humidity'].min()) if not df_original.empty else 0.0,
                    'max': float(df_original['humidity'].max()) if not df_original.empty else 0.0,
                    'median': float(df_original['humidity'].median()) if not df_original.empty else 0.0,
                    'std': float(df_original['humidity'].std()) if not df_original.empty else 0.0,
                    'count': len(df_original['humidity']),
                    'range': float(df_original['humidity'].max() - df_original['humidity'].min()) if not df_original.empty else 0.0,
                    'outliers': len(df_original[(df_original['humidity'] < THRESHOLDS['humidity']['min']) | (df_original['humidity'] > THRESHOLDS['humidity']['max'])])
                },
                'light_day': None,
                'light_night': None
            }
            stats['light_day'], stats['light_night'] = calculate_light_stats(df_original)

            sensor_performance = analyze_sensor_performance(df_original)

            latest_data = calculate_confidence_and_distance(df_original)

            alerts = check_thresholds(df_original)

            for _, row in df.iterrows():
                status = {}
                for col in ['temperature', 'humidity', 'light']:
                    val = float(row[col]) if pd.notna(row[col]) else 0.0
                    min_val = THRESHOLDS[col]['min']
                    max_val = THRESHOLDS[col]['max']
                    status[col] = 'danger' if val < min_val or val > max_val else 'warning' if val < min_val * 1.1 or val > max_val * 0.9 else 'success'
                table_rows.append({
                    'datetime': row['datetime'],
                    'temperature': val if col == 'temperature' else float(row['temperature']) if pd.notna(row['temperature']) else 0.0,
                    'humidity': val if col == 'humidity' else float(row['humidity']) if pd.notna(row['humidity']) else 0.0,
                    'light': val if col == 'light' else float(row['light']) if pd.notna(row['light']) else 0.0,
                    'status': status
                })

            generate_report(date_format=date_format)

        except Exception as e:
            flash(f'خطا در خواندن داده‌ها: {str(e)}')

    return render_template('index.html', table_rows=table_rows, stats=stats, alerts=alerts, 
                           start_date=start_date, end_date=end_date, 
                           table_start_date=table_start_date, table_end_date=table_end_date, 
                           temp_min_filter=temp_min_filter, temp_max_filter=temp_max_filter, 
                           hum_min_filter=hum_min_filter, hum_max_filter=hum_max_filter, 
                           light_min_filter=light_min_filter, light_max_filter=light_max_filter, 
                           date_format=date_format, thresholds=THRESHOLDS, 
                           latest_data=latest_data, sensor_performance=sensor_performance)

@app.route('/check_processing_status')
def check_processing_status():
    data_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    latest = None
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, parse_dates=['datetime']).tail(1)
        latest = calculate_confidence_and_distance(df)
    return jsonify({'status': 'complete', 'latest': latest})

@app.route('/update_thresholds', methods=['POST'])
def update_thresholds():
    global THRESHOLDS
    try:
        thresholds = {
            'temperature': {
                'min': float(request.form.get('temp_min', THRESHOLDS['temperature']['min'])),
                'max': float(request.form.get('temp_max', THRESHOLDS['temperature']['max']))
            },
            'humidity': {
                'min': float(request.form.get('hum_min', THRESHOLDS['humidity']['min'])),
                'max': float(request.form.get('hum_max', THRESHOLDS['humidity']['max']))
            },
            'light': {
                'min': float(request.form.get('light_min', THRESHOLDS['light']['min'])),
                'max': float(request.form.get('light_max', THRESHOLDS['light']['max']))
            }
        }
        if (thresholds['temperature']['min'] >= thresholds['temperature']['max'] or
            thresholds['humidity']['min'] >= thresholds['humidity']['max'] or
            thresholds['light']['min'] >= thresholds['light']['max']):
            flash('خطا: مقدار حداقل باید کمتر از مقدار حداکثر باشد.')
            return redirect(url_for('index', date_format=request.args.get('date_format', 'gregorian')))
        
        if save_thresholds(thresholds):
            THRESHOLDS.update(thresholds)
            date_format = request.args.get('date_format', 'gregorian')
            generate_report(date_format=date_format)
            flash('آستانه‌ها با موفقیت به‌روزرسانی شدند.')
        else:
            flash('خطا در ذخیره آستانه‌ها.')
        return redirect(url_for('index', date_format=date_format))
    except Exception as e:
        flash(f'خطا در به‌روزرسانی آستانه‌ها: {str(e)}')
        return redirect(url_for('index', date_format=request.args.get('date_format', 'gregorian')))

if __name__ == '__main__':
    app.run(debug=True)