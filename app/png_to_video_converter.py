import os
import imageio
import traceback
from config import logger

class PngToVideoConverter:
    def __init__(self, input_dir, output_dir, fps=16):
        """
        Initializes the converter with input and output directories and frames per second.
        
        :param input_dir: str, path to the root directory containing PNG files.
        :param output_dir: str, path to the directory where videos will be saved.
        :param fps: int, frames per second for the generated videos.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.fps = fps

    def find_all_png_folders(self):
        """
        Recursively searches for all folders containing PNG files.
        
        :return: list, paths of directories containing PNG images.
        """
        png_folders = []
        for root, _, files in os.walk(self.input_dir):
            png_files = [f for f in files if f.lower().endswith('.png')]
            if png_files:
                png_folders.append(root)
        return png_folders

    def create_video_from_images(self, image_files, output_path):
        """
        Creates a video from a list of image files.
        
        :param image_files: list, paths of PNG images to be compiled into a video.
        :param output_path: str, path where the generated video will be saved.
        """
        if not image_files:
            logger.warning(f"No PNG files found for processing.")
            return
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with imageio.get_writer(output_path, fps=self.fps, codec='libx264') as writer:
            for image_file in image_files:
                try:
                    image = imageio.imread(image_file)
                    writer.append_data(image)
                except Exception as e:
                    logger.error(f"Error reading {image_file}: {traceback.format_exception(e)}")
        
        logger.info(f"Video saved at: {output_path}")

    def process_images_to_video(self):
        """
        Finds all folders with PNG files and creates a video for each folder.
        """
        png_folders = self.find_all_png_folders()
        if not png_folders:
            logger.warning("No PNG files found.")
            return
        
        for folder in png_folders:
            png_files = [
                os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.png')
            ]
            if png_files:
                relative_path = os.path.relpath(folder, self.input_dir)
                parent_path, video_name = os.path.split(relative_path)
                video_name = f"{video_name}.mp4"
                output_folder = os.path.join(self.output_dir, parent_path)
                output_path = os.path.join(output_folder, video_name)
                self.create_video_from_images(png_files, output_path)