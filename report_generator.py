import pandas as pd
import plotly.graph_objects as go
import os
import jdatetime
from config import DATA_FOLDER, THRESHOLDS

def aggregate_data(df, aggregation):
    if aggregation == 'hourly':
        return df.groupby(df['datetime'].dt.floor('h')).agg({
            'temperature': 'mean', 'humidity': 'mean', 'light': 'mean'
        }).reset_index()
    elif aggregation == 'daily':
        df = df.groupby(df['datetime'].dt.date).agg({
            'temperature': 'mean', 'humidity': 'mean', 'light': 'mean'
        }).reset_index()
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    elif aggregation == 'weekly':
        df = df.groupby(df['datetime'].dt.isocalendar().week).agg({
            'temperature': 'mean', 'humidity': 'mean', 'light': 'mean', 'datetime': 'first'
        }).reset_index()
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    return df

def generate_summary(df, metrics, static_report_folder, date_format='gregorian'):
    with open(os.path.join(static_report_folder, 'summary.txt'), 'w', encoding='utf-8') as f:
        start_date = df['datetime'].min().strftime('%Y/%m/%d %H:%M') if date_format == 'gregorian' else jdatetime.datetime.fromgregorian(datetime=df['datetime'].min()).strftime('%Y/%m/%d %H:%M')
        end_date = df['datetime'].max().strftime('%Y/%m/%d %H:%M') if date_format == 'gregorian' else jdatetime.datetime.fromgregorian(datetime=df['datetime'].max()).strftime('%Y/%m/%d %H:%M')
        f.write(f"📊 خلاصه آماری داده‌های گلخانه خیار:\n")
        f.write(f"بازه زمانی: از {start_date} تا {end_date}\n\n")
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
            if col == 'temperature' and stats['mean'] < THRESHOLDS['temperature']['min']:
                f.write("توصیه: دمای پایین! سیستم گرمایش را بررسی کنید.\n")
            elif col == 'temperature' and stats['mean'] > THRESHOLDS['temperature']['max']:
                f.write("توصیه: دمای بالا! تهویه را تقویت کنید.\n")
            f.write("\n")

def generate_single_plot(df, col, info, aggregation, static_report_folder, date_format='gregorian'):
    fig = go.Figure()
    x_data = df['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M') if date_format == 'jalali' else x)
    fig.add_trace(go.Scatter(x=x_data, y=df[col], mode='lines', name=info['label'], line=dict(color=info['color'], width=2)))
    
    outliers = df[(df[col] < THRESHOLDS[col]['min']) | (df[col] > THRESHOLDS[col]['max'])]
    if not outliers.empty:
        x_data_outliers = outliers['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M') if date_format == 'jalali' else x)
        fig.add_trace(go.Scatter(x=x_data_outliers, y=outliers[col], mode='markers', name='نقاط خارج از آستانه', marker=dict(color='red', size=8, symbol='x')))
    
    max_point = df[df[col] == df[col].max()]
    min_point = df[df[col] == df[col].min()]
    x_max = max_point['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M') if date_format == 'jalali' else x)
    x_min = min_point['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M') if date_format == 'jalali' else x)
    fig.add_trace(go.Scatter(x=x_max, y=max_point[col], mode='markers+text', name='ماکسیمم', marker=dict(color='gold', size=10, symbol='star'), text=[f"Max: {max_point[col].iloc[0]:.2f}"], textposition="top center"))
    fig.add_trace(go.Scatter(x=x_min, y=min_point[col], mode='markers+text', name='مینیمم', marker=dict(color='purple', size=10, symbol='star'), text=[f"Min: {min_point[col].iloc[0]:.2f}"], textposition="bottom center"))
    
    fig.add_hline(y=df[col].mean(), line_dash="dot", line_color=info['color'], annotation_text=f"میانگین: {df[col].mean():.2f}", annotation_position="top left")
    fig.add_hline(y=THRESHOLDS[col]['min'], line_dash="dash", line_color="red", annotation_text=f"حداقل: {THRESHOLDS[col]['min']}", annotation_position="bottom right")
    fig.add_hline(y=THRESHOLDS[col]['max'], line_dash="dash", line_color="red", annotation_text=f"حداکثر: {THRESHOLDS[col]['max']}", annotation_position="top right")
    
    fig.update_layout(
        title=f'تغییرات {info["label"]} در زمان ({aggregation})',
        xaxis_title='زمان',
        yaxis_title=info['label'],
        yaxis=dict(range=info['range'], dtick=info['tick'], gridcolor='#dee2e6', gridwidth=2),
        xaxis=dict(tickformat='%Y/%m/%d %H:%M' if date_format == 'gregorian' else '%Y/%m/%d', tickangle=45, tickfont=dict(size=14), gridcolor='#dee2e6', gridwidth=2),
        template='plotly_white',
        font=dict(family="Vazir, sans-serif", size=16, color='#333'),
        hovermode='x unified',
        showlegend=True,
        xaxis_rangeslider_visible=True
    )
    fig.write_html(os.path.join(static_report_folder, f'{col}_plot_{aggregation}.html'))

def generate_combined_plot(df, selected_metrics, metrics, aggregation, combination, static_report_folder, date_format='gregorian'):
    fig_combined = go.Figure()
    for i, col in enumerate(selected_metrics):
        info = metrics[col]
        x_data = df['datetime'].apply(lambda x: jdatetime.datetime.fromgregorian(datetime=x).strftime('%Y/%m/%d %H:%M') if date_format == 'jalali' else x)
        fig_combined.add_trace(go.Scatter(x=x_data, y=df[col], mode='lines', name=info['label'], line=dict(color=info['color'], width=2), yaxis=f'y{i+1}'))
    
    layout = {
        'title': f'نمودار ترکیبی {", ".join([metrics[col]["label"] for col in selected_metrics])} ({aggregation})',
        'xaxis': dict(
            title='زمان',
            tickformat='%Y/%m/%d %H:%M' if date_format == 'gregorian' else '%Y/%m/%d',
            tickangle=45,
            tickfont=dict(size=14),
            gridcolor='#dee2e6',
            gridwidth=2,
            rangeslider=dict(visible=True),
            type='date'
        ),
        'template': 'plotly_white',
        'font': dict(family="Vazir, sans-serif", size=16, color='#333'),
        'hovermode': 'x unified',
        'showlegend': True
    }
    yaxes = {}
    for i, col in enumerate(selected_metrics):
        yaxes[f'yaxis{i+1}'] = dict(
            title=metrics[col]['label'],
            anchor="x",
            side="left" if i % 2 == 0 else "right",
            position=0.05 * i,
            overlaying="y" if i > 0 else None,
            range=metrics[col]['range'],
            dtick=metrics[col]['tick'],
            gridcolor='#dee2e6',
            gridwidth=2
        )
    layout.update(yaxes)
    fig_combined.update_layout(**layout)
    fig_combined.write_html(os.path.join(static_report_folder, f'combined_plot_{combination}_{aggregation}.html'))

def generate_report(data_path='greenhouse_clean.csv', aggregation='hourly', combination='all', date_format='gregorian'):
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
    
    df = aggregate_data(df, aggregation)
    
    metrics = {
        'temperature': {'label': 'دما (°C)', 'color': '#28A745', 'yaxis': 'y1', 'range': [max(0, df['temperature'].min() - 5), min(40, df['temperature'].max() + 5)], 'tick': 5},
        'humidity': {'label': 'رطوبت (%)', 'color': '#007BFF', 'yaxis': 'y2', 'range': [max(0, df['humidity'].min() - 10), min(100, df['humidity'].max() + 10)], 'tick': 10},
        'light': {'label': 'نور (Lux)', 'color': '#FFC107', 'yaxis': 'y3', 'range': [0, df['light'].max() + 1000], 'tick': 1000}
    }
    
    generate_summary(df, metrics, static_report_folder, date_format)
    for col, info in metrics.items():
        generate_single_plot(df, col, info, aggregation, static_report_folder, date_format)
    
    combinations = {
        'all': ['temperature', 'humidity', 'light'],
        'temp-hum': ['temperature', 'humidity'],
        'temp-light': ['temperature', 'light'],
        'hum-light': ['humidity', 'light']
    }
    selected_metrics = combinations.get(combination, ['temperature', 'humidity', 'light'])
    generate_combined_plot(df, selected_metrics, metrics, aggregation, combination, static_report_folder, date_format)
    
    print(f"✅ گزارش و نمودارها در پوشه {static_report_folder} ذخیره شد.")
    return True

if __name__ == '__main__':
    generate_report()