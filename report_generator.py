import pandas as pd
import plotly.graph_objects as go
import os
from config import DATA_FOLDER, THRESHOLDS

def generate_report(data_path='greenhouse_clean.csv', aggregation='hourly'):
    static_report_folder = os.path.join('static', 'report')
    os.makedirs(static_report_folder, exist_ok=True)
    data_path = os.path.join(DATA_FOLDER, data_path)
    
    if not os.path.exists(data_path):
        print(f"خطا: فایل {data_path} پیدا نشد.")
        return False
    
    try:
        df = pd.read_csv(data_path, parse_dates=['datetime'])
    except Exception as e:
        print(f"خطا در خواندن فایل CSV: {str(e)}")
        return False
    
    if len(df) > 10000:
        df = df.sample(n=10000, random_state=42).sort_values(by='datetime')
    
    # تجمیع داده‌ها
    if aggregation == 'hourly':
        df = df.groupby(df['datetime'].dt.floor('h')).agg({
            'temperature': 'mean',
            'humidity': 'mean',
            'light': 'mean'
        }).reset_index()
    elif aggregation == 'daily':
        df = df.groupby(df['datetime'].dt.date).agg({
            'temperature': 'mean',
            'humidity': 'mean',
            'light': 'mean'
        }).reset_index()
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif aggregation == 'weekly':
        df = df.groupby(df['datetime'].dt.isocalendar().week).agg({
            'temperature': 'mean',
            'humidity': 'mean',
            'light': 'mean',
            'datetime': 'first'
        }).reset_index()
    
    metrics = {
        'temperature': {'label': 'دما (°C)', 'color': '#FF5733', 'yaxis': 'y1'},
        'humidity': {'label': 'رطوبت (%)', 'color': '#33C4FF', 'yaxis': 'y2'},
        'light': {'label': 'نور (Lux)', 'color': '#33FF57', 'yaxis': 'y3'}
    }
    stats = {}
    with open(os.path.join(static_report_folder, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write("📊 خلاصه آماری داده‌های گلخانه:\n\n")
        for col, info in metrics.items():
            stats[col] = df[col].describe().to_dict()
            f.write(f"--- {info['label']} ---\n")
            f.write(f"میانگین: {stats[col]['mean']:.2f}\n")
            f.write(f"حداقل: {stats[col]['min']:.2f}\n")
            f.write(f"حداکثر: {stats[col]['max']:.2f}\n")
            f.write(f"انحراف معیار: {stats[col]['std']:.2f}\n")
            outliers = df[(df[col] < THRESHOLDS[col]['min']) | (df[col] > THRESHOLDS[col]['max'])][col].count()
            f.write(f"تعداد نقاط خارج از آستانه: {outliers}\n")
            if col == 'temperature':
                if stats[col]['mean'] < THRESHOLDS['temperature']['min']:
                    f.write("توصیه: دمای پایین! سیستم گرمایش را بررسی کنید.\n")
                elif stats[col]['mean'] > THRESHOLDS['temperature']['max']:
                    f.write("توصیه: دمای بالا! تهویه را تقویت کنید.\n")
            if col == 'humidity':
                if stats[col]['mean'] < THRESHOLDS['humidity']['min']:
                    f.write("توصیه: رطوبت پایین! سیستم رطوبت‌ساز را بررسی کنید.\n")
            if col == 'light':
                if stats[col]['mean'] < THRESHOLDS['light']['min']:
                    f.write("توصیه: نور بسیار کم! لامپ‌های رشد را بررسی کنید.\n")
            f.write("\n")
    
    # نمودارهای جداگانه
    for col, info in metrics.items():
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['datetime'], y=df[col], mode='lines', name=info['label'], 
            line=dict(color=info['color'])
        ))
        outliers = df[(df[col] < THRESHOLDS[col]['min']) | (df[col] > THRESHOLDS[col]['max'])]
        if not outliers.empty:
            fig.add_trace(go.Scatter(
                x=outliers['datetime'], y=outliers[col], mode='markers', 
                name='نقاط خارج از آستانه', marker=dict(color='red', size=8, symbol='x')
            ))
        max_point = df[df[col] == df[col].max()]
        min_point = df[df[col] == df[col].min()]
        fig.add_trace(go.Scatter(
            x=max_point['datetime'], y=max_point[col], mode='markers+text', 
            name='ماکسیمم', marker=dict(color='gold', size=10, symbol='star'), 
            text=[f"Max: {max_point[col].iloc[0]:.2f}"], textposition="top center"
        ))
        fig.add_trace(go.Scatter(
            x=min_point['datetime'], y=min_point[col], mode='markers+text', 
            name='مینیمم', marker=dict(color='purple', size=10, symbol='star'), 
            text=[f"Min: {min_point[col].iloc[0]:.2f}"], textposition="bottom center"
        ))
        fig.add_hline(y=stats[col]['mean'], line_dash="dot", line_color=info['color'], 
                      annotation_text=f"میانگین: {stats[col]['mean']:.2f}", 
                      annotation_position="top left")
        fig.add_hline(y=THRESHOLDS[col]['min'], line_dash="dash", line_color="red", 
                      annotation_text=f"حداقل: {THRESHOLDS[col]['min']}", 
                      annotation_position="bottom right")
        fig.add_hline(y=THRESHOLDS[col]['max'], line_dash="dash", line_color="red", 
                      annotation_text=f"حداکثر: {THRESHOLDS[col]['max']}", 
                      annotation_position="top right")
        fig.update_layout(
            title=f'تغییرات {info["label"]} در زمان ({aggregation})',
            xaxis_title='زمان',
            yaxis_title=info['label'],
            template='plotly_white',
            font=dict(family="Vazir, sans-serif", size=12),
            hovermode='x unified',
            showlegend=True,
            xaxis=dict(rangeslider=dict(visible=True), type='date')
        )
        fig.write_html(os.path.join(static_report_folder, f'{col}_plot_{aggregation}.html'))
    
    # نمودار ترکیبی
    fig_combined = go.Figure()
    for col, info in metrics.items():
        fig_combined.add_trace(go.Scatter(
            x=df['datetime'], y=df[col], mode='lines', name=info['label'], 
            line=dict(color=info['color']), yaxis=info['yaxis']
        ))
    fig_combined.update_layout(
        title=f'نمودار ترکیبی دما، رطوبت و نور ({aggregation})',
        xaxis=dict(title='زمان', rangeslider=dict(visible=True), type='date'),
        yaxis=dict(title='دما (°C)', anchor="x", side="left", position=0.0),
        yaxis2=dict(title='رطوبت (%)', anchor="x", overlaying="y", side="right", position=0.33),
        yaxis3=dict(title='نور (Lux)', anchor="x", overlaying="y", side="right", position=0.66),
        template='plotly_white',
        font=dict(family="Vazir, sans-serif", size=12),
        hovermode='x unified',
        showlegend=True
    )
    fig_combined.write_html(os.path.join(static_report_folder, f'combined_plot_{aggregation}.html'))

    print(f"✅ گزارش و نمودارها در پوشه {static_report_folder} ذخیره شد.")
    return True

if __name__ == '__main__':
    generate_report()