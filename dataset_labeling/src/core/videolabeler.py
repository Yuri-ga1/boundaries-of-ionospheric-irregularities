import tkinter as tk
import h5py
from PIL import Image, ImageTk
import os
import shutil
import cv2

from config import *

from custom_logger import Logger
from dataset_labeling.src.managers.h5datasetmanager import H5DatasetManager

class VideoLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Viewer")
        
        self.cap = None
        self.current_index = 0
        self.video_paths = self.get_all_video_paths()
        
        self.logger = Logger(
            filename=LOG_FILENAME,
            console_logging=CONSOLE_LOGGING
        )

        self.h5_manager = H5DatasetManager(self.logger, OMNI_PATH)
        
        self.setup_ui()
        self.play_video()
        self.update_frame()

    def setup_ui(self):
        self.title_var = tk.StringVar()
        self.title_label = tk.Label(self.root, textvariable=self.title_var, font=("Arial", 16))
        self.title_label.pack(pady=5)

        self.img_label = tk.Label(self.root)
        self.img_label.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.decline_btn = tk.Button(
            btn_frame, text="Decline", bg="red", fg="white",
            width=10, height=2, command=self.on_decline
        )
        self.decline_btn.pack(side="left", padx=10)

        self.accept_btn = tk.Button(
            btn_frame, text="Accept", bg="lime", fg="black",
            width=10, height=2, command=self.on_accept
        )
        self.accept_btn.pack(side="right", padx=10)

    def get_all_video_paths(self):
        paths = []
        for date in os.listdir(H5_FILE_PATH):
            date_path = os.path.join(H5_FILE_PATH, date)
            if not os.path.isdir(date_path):
                continue
            for station in os.listdir(date_path):
                station_path = os.path.join(date_path, station)
                if not os.path.isdir(station_path):
                    continue
                for file in os.listdir(station_path):
                    if file.lower().endswith(VIDEO_EXTENSIONS):
                        full_path = os.path.join(station_path, file)
                        paths.append((full_path, date, station))
        return paths

    def move_and_rename_video(self, target_folder):
        if self.current_index >= len(self.video_paths):
            return

        path, date, station = self.video_paths[self.current_index]
        file_name = os.path.basename(path)
        new_name = f"{station}_{file_name}"
        target_dir = os.path.join(target_folder)

        os.makedirs(target_dir, exist_ok=True)
        new_path = os.path.join(target_dir, new_name)
        shutil.move(path, new_path)

        station_path = os.path.join(H5_FILE_PATH, date, station)
        date_path = os.path.join(H5_FILE_PATH, date)

        try:
            if os.path.isdir(station_path) and not os.listdir(station_path):
                os.rmdir(station_path)
            if os.path.isdir(date_path) and not os.listdir(date_path):
                os.rmdir(date_path)
        except Exception as e:
            self.logger.error(f"Ошибка при удалении папок: {station_path} или {date_path}")

    def play_video(self):
        if self.cap is not None:
            self.cap.release()

        if self.current_index >= len(self.video_paths):
            self.title_var.set("Конец видео")
            return

        path, date, station = self.video_paths[self.current_index]
        file_name = os.path.basename(path)

        try:
            satellite, flyby, number = file_name.split("_")[:3]
            title = f"{date} {station} {satellite} {flyby} {number}"
        except:
            title = f"{date} {station} {file_name}"

        self.title_var.set(title)

        # if self.cap is not None:
        #     self.cap.release()
        self.cap = cv2.VideoCapture(path)

    def update_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()

            if ret:
                h, w = frame.shape[:2]
                scale = min(MAX_WIDTH / w, MAX_HEIGHT / h)
                new_w = int(w * scale)
                new_h = int(h * scale)

                resized_frame = cv2.resize(frame, (new_w, new_h))
                rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(Image.fromarray(rgb_frame))
                self.img_label.config(image=img)
                self.img_label.image = img

        self.root.after(UPDATE_DELAY, self.update_frame)

    def on_accept(self):
        self.process_video(ACCEPTED_FOLDER)

    def on_decline(self):
        self.process_video(DECLINED_FOLDER)

    def process_video(self, target_folder):
        if self.current_index >= len(self.video_paths):
            return

        if self.cap is not None:
            self.cap.release()

        path, date, station = self.video_paths[self.current_index]
        file_name = os.path.basename(path)[:-4]

        if target_folder == ACCEPTED_FOLDER:
            try:
                satellite, flyby, number = file_name.split("_")
                fb = f"{flyby}_{number}"
                
                full_h5_file_path = os.path.join(H5_FILE_PATH, f"{date}.h5")

                roti, timestamps, lon, lat, event_times, event_types = self.h5_manager.get_metadata_from_h5(
                    full_h5_file_path, station, satellite, fb
                )

                all_datasets = self.h5_manager.calculate_all_parameters(
                    roti=roti,
                    timestamps=timestamps,
                    lat=lat,
                    lon=lon,
                    date=date
                )

                relative_key = f"{date}_{station}_{file_name}"
                
                self.h5_manager.save_data_to_h5_dataset(
                    DATASET_H5_PATH, 
                    relative_key, 
                    event_times, 
                    event_types, 
                    **all_datasets
                )

                self.logger.info(f"Успешно сохранены данные для: {relative_key}")

            except Exception as e:
                self.logger.error(f"Ошибка при разборе имени файла или метаданных: {e}")

        self.move_and_rename_video(target_folder)
        self.current_index += 1
        self.play_video()