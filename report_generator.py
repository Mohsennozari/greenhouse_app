import pandas as pd
import plotly.graph_objects as go
import os
from config import DATA_FOLDER, THRESHOLDS

def generate_report(data_path='greenhouse_clean.csv', aggregation='hourly', combination='all'):
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
        df['datetime'] = pd.to_datetime(df['datetime'])
    
    # مشخص کردن ساعات شب (8 شب تا 6 صبح)
    df['is_night'] = df['datetime'].dt.hour.between(20, 23) | df['datetime'].dt.hour.between(0, 5)
    
    metrics = {
        'temperature': {
            'label': 'دما (°C)', 
            'color': '#28A745', 
            'yaxis': 'y1',
            'range': [max(0, df['temperature'].min() - 5), min(40, df['temperature'].max() + 5)],
            'tick': 5
        },
        'humidity': {
            'label': 'رطوبت (%)', 
            'color': '#007BFF', 
            'yaxis': 'y2',
            'range': [max(0, df['humidity'].min() - 10), min(100, df['humidity'].max() + 10)],
            'tick': 10
        },
        'light': {
            'label': 'نور (Lux)', 
            'color': '#FFC107', 
            'yaxis': 'y3',
            'range': [0, df['light'].max() + 1000],
            'tick': 1000
        }
    }
    
    # ذخیره اطلاعات گلخانه
    greenhouse_info = {
        'name': 'گلخانه خیار',
        'data_range': f"از {df['datetime'].min().strftime('%Y-%m-%d')} تا {df['datetime'].max().strftime('%Y-%m-%d')}"
    }
    
    # گزارش متنی
    with open(os.path.join(static_report_folder, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write(f"📊 خلاصه آماری داده‌های {greenhouse_info['name']}:\n")
        f.write(f"بازه زمانی: {greenhouse_info['data_range']}\n\n")
        for col, info in metrics.items():
            stats = df[col].describe().to_dict()
            stats['median'] = df[col].median()
            stats['range'] = df[col].max() - df[col].min()
            f.write(f"--- {info['label']} ---\n")
            f.write(f"میانگین: {stats['mean']:.2f}\n")
            f.write(f"حداقل: {stats['min']:.2f}\n")
            f.write(f"حداکثر: {stats['max']:.2f}\n")
            f.write(f"میانه: {stats['median']:.2f}\n")
            f.write(f"دامنه: {stats['range']:.2f}\n")
            f.write(f"تعداد رکوردها: {stats['count']:.0f}\n")
            f.write(f"انحراف معیار: {stats['std']:.2f}\n")
            outliers = df[(df[col] < THRESHOLDS[col]['min']) | (df[col] > THRESHOLDS[col]['max'])][col].count()
            f.write(f"تعداد نقاط خارج از آستانه: {outliers}\n")
            if col == 'light':
                night_outliers = df[df['is_night'] & (df[col] > 100)][col].count()
                f.write(f"تعداد نقاط نور غیرعادی در شب: {night_outliers}\n")
            if col == 'temperature':
                if stats['mean'] < THRESHOLDS['temperature']['min']:
                    f.write("توصیه: دمای پایین! سیستم گرمایش را بررسی کنید.\n")
                elif stats['mean'] > THRESHOLDS['temperature']['max']:
                    f.write("توصیه: دمای بالا! تهویه را تقویت کنید.\n")
            if col == 'humidity':
                if stats['mean'] < THRESHOLDS['humidity']['min']:
                    f.write("توصیه: رطوبت پایین! سیستم رطوبت‌ساز را بررسی کنید.\n")
            if col == 'light':
                if stats['mean'] < THRESHOLDS['light']['min']:
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
        if col == 'light':
            night_outliers = df[df['is_night'] & (df[col] > 100)]
            if not night_outliers.empty:
                fig.add_trace(go.Scatter(
                    x=night_outliers['datetime'], y=night_outliers[col], mode='markers', 
                    name='نور غیرعادی در شب', marker=dict(color='orange', size=8, symbol='circle')
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
        fig.add_hline(y=stats['mean'], line_dash="dot", line_color=info['color'], 
                      annotation_text=f"میانگین: {stats['mean']:.2f}", 
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
            yaxis=dict(range=info['range'], dtick=info['tick']),
            template='plotly_white',
            font=dict(family="Vazir, sans-serif", size=12),
            hovermode='x unified',
            showlegend=True,
            xaxis=dict(rangeslider=dict(visible=True), type='date')
        )
        fig.write_html(os.path.join(static_report_folder, f'{col}_plot_{aggregation}.html'))
    
    # نمودارهای ترکیبی
    combinations = {
        'all': ['temperature', 'humidity', 'light'],
        'temp-hum': ['temperature', 'humidity'],
        'temp-light': ['temperature', 'light'],
        'hum-light': ['humidity', 'light']
    }
    selected_metrics = combinations.get(combination, ['temperature', 'humidity', 'light'])
    
    fig_combined = go.Figure()
    for i, col in enumerate(selected_metrics):
        info = metrics[col]
        fig_combined.add_trace(go.Scatter(
            x=df['datetime'], y=df[col], mode='lines', name=info['label'], 
            line=dict(color=info['color']), yaxis=f'y{i+1}'
        ))
    layout = {
        'title': f'نمودار ترکیبی {", ".join([metrics[col]["label"] for col in selected_metrics])} ({aggregation})',
        'xaxis': dict(title='زمان', rangeslider=dict(visible=True), type='date'),
        'template': 'plotly_white',
        'font': dict(family="Vazir, sans-serif", size=12),
        'hovermode': 'x unified',
        'showlegend': True
    }
    yaxes = {}
    for i, col in enumerate(selected_metrics):
        yaxes[f'yaxis{i+1}'] = dict(
            title=metrics[col]['label'],
            anchor="x",
            side="left" if i == 0 else "right",
            position=0.0 if i == 0 else 0.33 * i,
            overlaying="y" if i > 0 else None,
            range=metrics[col]['range'],
            dtick=metrics[col]['tick']
        )
    layout.update(yaxes)
    fig_combined.update_layout(**layout)
    fig_combined.write_html(os.path.join(static_report_folder, f'combined_plot_{combination}_{aggregation}.html'))

    print(f"✅ گزارش و نمودارها در پوشه {static_report_folder} ذخیره شد.")
    return True

if __name__ == '__main__':
    generate_report()