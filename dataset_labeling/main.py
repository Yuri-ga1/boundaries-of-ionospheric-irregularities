import tkinter as tk
from video_labeler import VideoLabeler

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoLabeler(root)
    root.mainloop()