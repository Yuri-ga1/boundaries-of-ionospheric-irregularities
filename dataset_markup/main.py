import tkinter as tk
import h5py
from PIL import Image, ImageTk
import os
import shutil
import cv2

from custom_logger import Logger

ROOT_DIR = "video"

logger = Logger(
    filename="logs.log",
    console_logging=False
)

cap = None  # глобальный видеопоток


def move_and_rename_video(target_folder):
    if current_index[0] >= len(video_paths):
        return

    path, date, station = video_paths[current_index[0]]
    file_name = os.path.basename(path)
    new_name = f"{station}_{file_name}"
    target_dir = os.path.join(target_folder)

    os.makedirs(target_dir, exist_ok=True)
    new_path = os.path.join(target_dir, new_name)
    shutil.move(path, new_path)

    station_path = os.path.join(ROOT_DIR, date, station)
    date_path = os.path.join(ROOT_DIR, date)

    try:
        if os.path.isdir(station_path) and not os.listdir(station_path):
            os.rmdir(station_path)
        if os.path.isdir(date_path) and not os.listdir(date_path):
            os.rmdir(date_path)
    except Exception as e:
        logger.error(f"Ошибка при удалении папок: {station_path} or {date_path}")


def get_all_video_paths():
    paths = []
    for date in os.listdir(ROOT_DIR):
        date_path = os.path.join(ROOT_DIR, date)
        if not os.path.isdir(date_path):
            continue
        for station in os.listdir(date_path):
            station_path = os.path.join(date_path, station)
            if not os.path.isdir(station_path):
                continue
            for file in os.listdir(station_path):
                if file.lower().endswith((".mp4", ".avi", ".mov")):
                    full_path = os.path.join(station_path, file)
                    paths.append((full_path, date, station))
    return paths


def play_video():
    global cap
    if cap is not None:
        cap.release()

    if current_index[0] >= len(video_paths):
        title_var.set("Конец видео")
        return

    path, date, station = video_paths[current_index[0]]
    file_name = os.path.basename(path)

    try:
        satellite, flyby, number = file_name.split("_")[:3]
        title = f"{date} {station} {satellite} {flyby} {number}"
    except:
        title = f"{date} {station} {file_name}"

    title_var.set(title)

    if cap is not None:
        cap.release()
    cap = cv2.VideoCapture(path)


MAX_WIDTH = 640*1.5
MAX_HEIGHT = 480*1.5

def update_frame():
    if cap is not None and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()

        if ret:
            # Получаем оригинальные размеры
            h, w = frame.shape[:2]
            scale = min(MAX_WIDTH / w, MAX_HEIGHT / h)
            new_w = int(w * scale)
            new_h = int(h * scale)

            # Масштабируем кадр
            resized_frame = cv2.resize(frame, (new_w, new_h))

            # Конвертируем и показываем
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(rgb_frame))
            img_label.config(image=img)
            img_label.image = img

    root.after(110, update_frame)


def get_metadata_from_h5(file_path, station, satellite, fb):
    """Извлекает данные из группы HDF5 файла."""
    try:
        with h5py.File(file_path, 'r') as h5file:
            if station in h5file:
                station_h5file = h5file[station]
                if satellite in station_h5file:
                    satellite_h5file = station_h5file[satellite]
                    if fb in satellite_h5file:
                        group = satellite_h5file[fb]

                        times = group.attrs.get('times', [])
                        types = group.attrs.get('types', [])

                        roti = group.get('roti', None)
                        timestamps = group.get('timestamps', None)

                        if roti is not None:
                            roti = roti[:]  # Извлекаем данные из датасета в массив
                        if timestamps is not None:
                            timestamps = timestamps[:]
                        return times, types, roti, timestamps
    except Exception as e:
        logger.error(f"Ошибка при чтении HDF5 файла: {station}_{satellite}_{fb}")
        return [], [], None, None
    
def save_data_to_h5_dataset(new_file_path, group_path, times, types, roti, timestamps):
    """Сохраняет извлеченные данные в новый HDF5 файл."""
    try:
        with h5py.File(new_file_path, 'a') as h5file:
            if group_path not in h5file:
                group = h5file.create_group(group_path)
                # Сохраняем атрибуты
                group.attrs['times'] = times
                group.attrs['types'] = types
                
                # Проверяем и сохраняем другие данные как datasets
                if roti is not None and len(roti) > 0:
                    group.create_dataset('roti', data=roti)
                else:
                    logger.warning(f"roti пусто или None, не сохраняем {group_path}")

                if timestamps is not None and len(timestamps) > 0:
                    group.create_dataset('timestamps', data=timestamps)
                else:
                    logger.warning(f"timestamps пусто или None, не сохраняем {group_path}")
                    
    except Exception as e:
        logger.error(f"Ошибка при записи в новый HDF5 файл: {group_path}")

def on_accept():
    global cap
    if current_index[0] >= len(video_paths):
        return

    if cap is not None:
        cap.release()

    path, date, station = video_paths[current_index[0]]
    file_name = os.path.basename(path)[:-4]

    try:

        satellite, flyby, number = file_name.split("_")
        fb = f"{flyby}_{number}"
        
        # Путь к исходному HDF5 файлу
        h5_file_path = os.path.join(ROOT_DIR, date, f"{date}.h5")

        # Получаем метаданные из HDF5
        times, events, roti, timestamps = get_metadata_from_h5(h5_file_path, station, satellite, fb)

        # Путь к новому HDF5 файлу
        new_dataset = os.path.join("dataset.h5")

        relative_key = f"{date}_{station}_{file_name}"
        # Сохраняем данные в новый HDF5 файл
        save_data_to_h5_dataset(new_dataset, relative_key, times, events, roti, timestamps)

    except Exception as e:
        logger.error(f"Ошибка при разборе имени файла или метаданных: {station}_{satellite}_{fb}")

    move_and_rename_video("accepted")
    current_index[0] += 1
    play_video()


def on_decline():
    global cap
    if current_index[0] >= len(video_paths):
        return

    if cap is not None:
        cap.release()

    move_and_rename_video("declined")
    current_index[0] += 1
    play_video()


# === Глобальные переменные ===
video_paths = get_all_video_paths()
current_index = [0]

# === Интерфейс ===
root = tk.Tk()
root.title("Video Viewer")

title_var = tk.StringVar()
title_label = tk.Label(root, textvariable=title_var, font=("Arial", 16))
title_label.pack(pady=5)

img_label = tk.Label(root)
img_label.pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

decline_btn = tk.Button(btn_frame, text="Decline", bg="red", fg="white", width=10, height=2, command=on_decline)
decline_btn.pack(side="left", padx=10)

accept_btn = tk.Button(btn_frame, text="Accept", bg="lime", fg="black", width=10, height=2, command=on_accept)
accept_btn.pack(side="right", padx=10)

# === Запуск ===
play_video()
update_frame()

root.mainloop()
