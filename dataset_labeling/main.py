import tkinter as tk
from dataset_labeling.src.core.videolabeler import VideoLabeler

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoLabeler(root)
    root.mainloop()