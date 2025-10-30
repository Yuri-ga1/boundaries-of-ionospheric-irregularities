import os
import imageio
import traceback
import shutil
from config import logger

class PngToVideoConverter:
    def __init__(self, input_dir, output_dir, fps=16, remove_png_after_convert=False):
        """
        Initializes the converter with input and output directories and frames per second.
        
        :param input_dir: str, path to the root directory containing PNG files.
        :param output_dir: str, path to the directory where videos will be saved.
        :param fps: int, frames per second for the generated videos.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.fps = fps
        self.remove_png_after_convert = remove_png_after_convert

    def find_all_png_folders(self):
        """
        Recursively searches for all folders containing PNG files.
        
        :return: list, paths of directories containing PNG images.
        """
        png_folders = []
        for root, _, files in os.walk(self.input_dir):
            if any(f.lower().endswith('.png') for f in files):
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
            return False
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with imageio.get_writer(output_path, fps=self.fps, codec='libx264') as writer:
                for image_file in sorted(image_files):
                    try:
                        image = imageio.imread(image_file)
                        writer.append_data(image)
                    except Exception as e:
                        logger.error(f"Error reading {image_file}: {traceback.format_exception(e)}")
            
            logger.info(f"Video saved at: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating video {output_path}: {traceback.format_exc()}")
            return False

    def remove_png_folder(self, folder_path):
        """
        Removes the PNG folder after successful video creation.
        
        :param folder_path: str, path to the folder containing PNG files to remove
        """
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                logger.info(f"Successfully removed PNG folder: {folder_path}")
                return True
            else:
                logger.warning(f"Folder doesn't exist, cannot remove: {folder_path}")
                return False
        except Exception as e:
            logger.error(f"Error removing folder {folder_path}: {traceback.format_exc()}")
            return False

    def remove_empty_parent_folders(self, folder_path):
        """
        Recursively removes empty parent folders up to the input directory.
        
        :param folder_path: str, path to start checking for empty folders
        """
        current_dir = folder_path
        input_dir = os.path.abspath(self.input_dir)
        
        while current_dir != input_dir and os.path.exists(current_dir):
            try:
                if not os.listdir(current_dir):
                    os.rmdir(current_dir)
                    logger.info(f"Removed empty directory: {current_dir}")
                    current_dir = os.path.dirname(current_dir)
                else:
                    break
            except Exception as e:
                logger.warning(f"Could not remove directory {current_dir}: {e}")
                break

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
            if not png_files:
                continue
            
            
            relative_path = os.path.relpath(folder, self.input_dir)
            path_parts = relative_path.split(os.sep)

            if len(path_parts) < 2:
                logger.warning(f"Skipping folder without substructure: {folder}")
                continue
            
            output_subfolder = os.path.join(self.output_dir, path_parts[0])
            video_name = "_".join(path_parts[1:]) + ".mp4"
            output_path = os.path.join(output_subfolder, video_name)

            success = self.create_video_from_images(png_files, output_path)

            if success and self.remove_png_after_convert:
                removal_success = self.remove_png_folder(folder)
                
                # Optionally remove empty parent folders
                if removal_success:
                    parent_dir = os.path.dirname(folder)
                    self.remove_empty_parent_folders(parent_dir)
