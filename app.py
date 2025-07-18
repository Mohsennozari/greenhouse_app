from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
from config import DATA_FOLDER, THRESHOLDS
from report_generator import generate_report
from preprocess import preprocess_data

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_key')

def check_thresholds(df):
    alerts = {'temperature': False, 'humidity': False, 'light': False}
    if not df.empty:
        latest = df.iloc[-1]
        if latest['temperature'] < THRESHOLDS['temperature']['min'] or latest['temperature'] > THRESHOLDS['temperature']['max']:
            alerts['temperature'] = True
        if latest['humidity'] < THRESHOLDS['humidity']['min'] or latest['humidity'] > THRESHOLDS['humidity']['max']:
            alerts['humidity'] = True
        if latest['light'] < THRESHOLDS['light']['min'] or latest['light'] > THRESHOLDS['light']['max']:
            alerts['light'] = True
    return alerts

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    aggregation = request.args.get('aggregation', 'hourly')
    data_path = os.path.join(DATA_FOLDER, 'greenhouse_clean.csv')
    
    table_data = None
    stats = None
    alerts = {'temperature': False, 'humidity': False, 'light': False}
    total_pages = 1
    charts_available = {
        'temperature': os.path.exists(os.path.join(app.static_folder, 'report', f'temperature_plot_{aggregation}.html')),
        'humidity': os.path.exists(os.path.join(app.static_folder, 'report', f'humidity_plot_{aggregation}.html')),
        'light': os.path.exists(os.path.join(app.static_folder, 'report', f'light_plot_{aggregation}.html')),
        'combined': os.path.exists(os.path.join(app.static_folder, 'report', f'combined_plot_{aggregation}.html'))
    }
    
    if os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path, parse_dates=['datetime'])
            filtered_data_path = 'greenhouse_clean.csv'
            if start_date and end_date:
                try:
                    df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
                    filtered_data_path = 'filtered_data.csv'
                    df.to_csv(os.path.join(DATA_FOLDER, filtered_data_path), index=False)
                    generate_report(data_path=filtered_data_path, aggregation=aggregation)
                except Exception as e:
                    flash(f'خطا در فیلتر زمانی: {str(e)}')
            else:
                generate_report(data_path=filtered_data_path, aggregation=aggregation)
            stats = {
                'temperature': df['temperature'].describe().to_dict(),
                'humidity': df['humidity'].describe().to_dict(),
                'light': df['light'].describe().to_dict()
            }
            total_rows = len(df)
            start = (page - 1) * per_page
            end = min(start + per_page, total_rows)
            table_data = df.iloc[start:end].to_html(classes='table table-striped', index=False, border=0)
            total_pages = (total_rows + per_page - 1) // per_page
            alerts = check_thresholds(df)
        except Exception as e:
            flash(f'خطا در خواندن داده‌ها: {str(e)}')
    
    return render_template('index.html', table_data=table_data, stats=stats, alerts=alerts, 
                           page=page, total_pages=total_pages, start_date=start_date, 
                           end_date=end_date, aggregation=aggregation, charts_available=charts_available)

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
        file.save(filepath)
        if preprocess_data():
            generate_report(aggregation='hourly')
            flash('فایل با موفقیت آپلود و پردازش شد.')
        else:
            flash('خطا در پردازش فایل.')
        return redirect(url_for('index'))
    else:
        flash('لطفاً فقط فایل CSV انتخاب کنید.')
        return redirect(url_for('index'))

@app.route('/download_summary')
def download_summary():
    summary_path = os.path.join(app.static_folder, 'report', 'summary.txt')
    if os.path.exists(summary_path):
        return send_file(summary_path, as_attachment=True)
    flash('گزارش در دسترس نیست.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)