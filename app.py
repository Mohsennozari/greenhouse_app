from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_caching import Cache
from dotenv import load_dotenv
import pandas as pd
import os
import jdatetime
from config import DATA_FOLDER, THRESHOLDS, save_thresholds
from report_generator import generate_report
from preprocess import preprocess_data

# بارگذاری متغیرهای محیطی
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("کلید مخفی Flask تنظیم نشده است. لطفاً FLASK_SECRET_KEY را در فایل .env یا متغیرهای محیطی تنظیم کنید.")

app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

def validate_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        required_columns = ['datetime', 'temperature', 'humidity', 'light']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("فایل CSV ستون‌های موردنیاز را ندارد.")
        return True
    except Exception as e:
        flash(f"خطا در اعتبارسنجی فایل CSV: {str(e)}")
        return False

def check_thresholds(df):
    alerts = {'temperature': False, 'humidity': False, 'light': False}
    if not df.empty:
        latest = df.iloc[-1]
        for metric in alerts:
            if latest[metric] < THRESHOLDS[metric]['min'] or latest[metric] > THRESHOLDS[metric]['max']:
                alerts[metric] = True
    return alerts

def analyze_sensor_issues(df):
    sensor_issues = {'outliers': 0}
    if not df.empty:
        sensor_issues['outliers'] = df[(df['light'] < THRESHOLDS['light']['min']) | (df['light'] > THRESHOLDS['light']['max'])]['light'].count()
    return sensor_issues

@app.route('/')
@cache.cached(timeout=3600, query_string=True)
def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    aggregation = request.args.get('aggregation', 'hourly')
    combination = request.args.get('combination', 'all')
    date_format = request.args.get('date_format', 'gregorian')

    data_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    table_rows = []
    stats = None
    alerts = {'temperature': False, 'humidity': False, 'light': False}
    sensor_issues = {'outliers': 0}
    latest_data = None
    total_pages = 1
    greenhouse_info = {'name': 'گلخانه خیار', 'data_range': 'نامشخص'}
    
    charts_available = {
        'temperature': os.path.exists(os.path.join(app.static_folder, 'report', f'temperature_plot_{aggregation}.html')),
        'humidity': os.path.exists(os.path.join(app.static_folder, 'report', f'humidity_plot_{aggregation}.html')),
        'light': os.path.exists(os.path.join(app.static_folder, 'report', f'light_plot_{aggregation}.html')),
        'combined': os.path.exists(os.path.join(app.static_folder, 'report', f'combined_plot_{combination}_{aggregation}.html'))
    }

    if os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path, parse_dates=['datetime']).tail(1000)
            if date_format == 'jalali':
                df['datetime'] = df['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M:%S'))
            greenhouse_info['data_range'] = f"از {df['datetime'].min()} تا {df['datetime'].max()}"
            filtered_data_path = 'greenhouse_clean.csv'

            if start_date and end_date:
                try:
                    if date_format == 'jalali':
                        start_date = jdatetime.datetime.strptime(start_date, '%Y/%m/%d').togregorian().strftime('%Y-%m-%d')
                        end_date = jdatetime.datetime.strptime(end_date, '%Y/%m/%d').togregorian().strftime('%Y-%m-%d')
                    df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
                    filtered_data_path = 'filtered_data.csv'
                    df.to_csv(os.path.join(DATA_FOLDER, filtered_data_path), index=False)
                    generate_report(data_path=filtered_data_path, aggregation=aggregation, combination=combination)
                except ValueError as e:
                    flash(f'خطا در فرمت تاریخ: {str(e)}')
            else:
                generate_report(data_path=filtered_data_path, aggregation=aggregation, combination=combination)

            stats = {
                'temperature': {
                    'mean': df['temperature'].mean(),
                    'min': df['temperature'].min(),
                    'max': df['temperature'].max(),
                    'median': df['temperature'].median(),
                    'range': df['temperature'].max() - df['temperature'].min(),
                    'count': df['temperature'].count(),
                    'std': df['temperature'].std()
                },
                'humidity': {
                    'mean': df['humidity'].mean(),
                    'min': df['humidity'].min(),
                    'max': df['humidity'].max(),
                    'median': df['humidity'].median(),
                    'range': df['humidity'].max() - df['humidity'].min(),
                    'count': df['humidity'].count(),
                    'std': df['humidity'].std()
                },
                'light': {
                    'mean': df['light'].mean(),
                    'min': df['light'].min(),
                    'max': df['light'].max(),
                    'median': df['light'].median(),
                    'range': df['light'].max() - df['light'].min(),
                    'count': df['light'].count(),
                    'std': df['light'].std()
                }
            }

            total_rows = len(df)
            start = (page - 1) * per_page
            end = min(start + per_page, total_rows)
            latest_data = df.iloc[-1].to_dict() if not df.empty else None
            alerts = check_thresholds(df)
            sensor_issues = analyze_sensor_issues(df)

            for _, row in df.iloc[start:end].iterrows():
                status = {}
                for col in ['temperature', 'humidity', 'light']:
                    val = row[col]
                    min_val = THRESHOLDS[col]['min']
                    max_val = THRESHOLDS[col]['max']
                    status[col] = 'danger' if val < min_val or val > max_val else 'warning' if min_val * 1.1 > val or max_val * 0.9 < val else 'success'
                table_rows.append({
                    'datetime': row['datetime'],
                    'temperature': row['temperature'],
                    'humidity': row['humidity'],
                    'light': row['light'],
                    'status': status
                })
            total_pages = (total_rows + per_page - 1) // per_page

        except Exception as e:
            flash(f'خطا در خواندن داده‌ها: {str(e)}')

    return render_template('index.html', table_rows=table_rows, stats=stats, alerts=alerts, 
                           page=page, total_pages=total_pages, start_date=start_date, 
                           end_date=end_date, aggregation=aggregation, combination=combination,
                           date_format=date_format, greenhouse_info=greenhouse_info,
                           charts_available=charts_available, thresholds=THRESHOLDS, 
                           sensor_issues=sensor_issues, latest_data=latest_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('هیچ فایلی انتخاب نشده است.')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('نام فایل معتبر نیست.')
        return redirect(url_for('index'))

    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(DATA_FOLDER, 'greenhouse_raw.csv')
        try:
            file.save(filepath)
            if validate_csv(filepath) and preprocess_data():
                generate_report(aggregation='hourly', combination='all')
                flash('فایل با موفقیت آپلود و پردازش شد.')
            else:
                flash('خطا در پردازش فایل.')
        except Exception as e:
            flash(f'خطا در ذخیره فایل: {str(e)}')
        return redirect(url_for('index'))
    flash('لطفاً فقط فایل CSV انتخاب کنید.')
    return redirect(url_for('index'))

@app.route('/update_thresholds', methods=['POST'])
def update_thresholds():
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
        if save_thresholds(thresholds):
            flash('آستانه‌ها با موفقیت به‌روزرسانی شدند.')
        else:
            flash('خطا در ذخیره آستانه‌ها.')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'خطا در به‌روزرسانی آستانه‌ها: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download_summary')
def download_summary():
    summary_path = os.path.join(app.static_folder, 'report', 'summary.txt')
    if os.path.exists(summary_path):
        return send_file(summary_path, as_attachment=True)
    flash('گزارش در دسترس نیست.')
    return redirect(url_for('index'))

@app.route('/check_processing_status')
def check_processing_status():
    return {'status': 'complete'}

if __name__ == '__main__':
    app.run(debug=True)