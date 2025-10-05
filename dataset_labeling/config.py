import os

# Пути
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_PATH = os.path.join(SCRIPT_DIR, '..', 'files')

H5_FILE_PATH = os.path.join(FILES_PATH, "processed_flybys")
DATASET_H5_PATH = os.path.join(FILES_PATH, "datasets", "dataset.h5")

VIDEO_PATH = os.path.join(FILES_PATH, "video")
ACCEPTED_FOLDER = os.path.join(VIDEO_PATH, "accepted")
DECLINED_FOLDER = os.path.join(VIDEO_PATH, "declined")

# Настройки отображения
MAX_WIDTH = 640 * 1.5
MAX_HEIGHT = 480 * 1.5
UPDATE_DELAY = 110  # ms

# Настройки логгера
LOG_FILENAME = "dataset-labeling.log"
CONSOLE_LOGGING = False

# Поддерживаемые видеоформаты
VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov")