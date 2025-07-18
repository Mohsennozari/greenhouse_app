import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
REPORT_FOLDER = os.path.join(STATIC_FOLDER, 'report')

THRESHOLDS = {
    'temperature': {'min': 18.0, 'max': 28.0},
    'humidity': {'min': 40.0, 'max': 70.0},
    'light': {'min': 3000, 'max': 7000}
}