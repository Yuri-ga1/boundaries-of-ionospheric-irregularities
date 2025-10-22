LON_CONDITION = -60
LAT_CONDITION = 40

SEGMENT_LON_STEP = 0.2
SEGMENT_LAT_STEP = 0.7

BOUNDARY_CONDITION = 0.07

WINDOW_WIDTH = 10
WINDOW_AREA = 50

RE_KM = 6356
HM = 300

MIN_CLUSTER_SIZE = 100

TIME_GAP_LIMIT = 15 #minutes

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_PATH = os.path.join(SCRIPT_DIR, '..', 'files')

MAP_PATH =  os.path.join(FILES_PATH, "map")
BOUNDARY_PATH = os.path.join(FILES_PATH, 'boundary')
FLYBYS_PATH = os.path.join(FILES_PATH, "flybys")
PROCESSED_FLYBYS_PATH = os.path.join(FILES_PATH, "processed_flybys")

os.makedirs(MAP_PATH, exist_ok=True)
os.makedirs(BOUNDARY_PATH, exist_ok=True)
os.makedirs(FLYBYS_PATH, exist_ok=True)
os.makedirs(PROCESSED_FLYBYS_PATH, exist_ok=True)

GRAPHS_PATH = os.path.join(FILES_PATH, 'graphs')
FRAME_GRAPHS_PATH = os.path.join(GRAPHS_PATH, 'combined')
SAVE_VIDEO_PATH = os.path.join(GRAPHS_PATH, 'video')

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_logger import Logger

logger = Logger(
    filename="gnss_processor.log",
    console_logging=False
)

#--------------------------------------------------------------------------------

# Обработка RINEX файлов
TIME_DIFF_THRESHOLD_SECONDS = 1800  # Порог для разделения пролетов (30 минут)
MIN_ELEVATION_DEGREES = 10  # Минимальный угол возвышения
MAP_TIME_STEP_SECONDS = 300  # Временной шаг для карт (5 минут)

# Координатные ограничения для станций
COORDINATE_BOUNDS = {
    'min_lat': 0,
    'max_lat': 90,
    'min_lon': -2.53073,
    'max_lon': -0.523599
}

# Обработка карт и границ
GRID_POINTS = 100  # Количество точек для интерполяционной сетки
DBSCAN_EPS = 0.7  # Параметр eps для DBSCAN
DBSCAN_MIN_SAMPLES = 3  # Минимальное количество samples для DBSCAN
MAX_LATITUDE = 90  # Максимальная широта для северного полушария

# Общие пределы для графиков
COMMON_X_LIMITS = (-120, LON_CONDITION)
COMMON_Y_LIMITS = (LAT_CONDITION, 90)

# Цветовые схемы для событий
COLOR_MAPPINGS = {
    "entered": "green",
    "exited": "red", 
    "noise": "yellow"
}

# Конфигурация графиков
PLOT_CONFIGS = {
    'figure_size': (16, 12),
    'colormap': 'coolwarm',
    'normalization_range': (0, 0.1)
}

# Расчет траекторий спутников
ARTIFICIAL_POINTS_INTERVAL_MINUTES = 10  # Интервал для вставки искусственных точек
ARTIFICIAL_POINTS_OFFSET_SECONDS = 30    # Смещение искусственных точек от середины промежутка