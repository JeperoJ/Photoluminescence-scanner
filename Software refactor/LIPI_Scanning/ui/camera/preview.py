import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
import time
import threading
from threading import Lock
import numpy as np
from PIL import Image, ImageTk
from ...src import camera_utils

import FliSdk_V2


class Processor:
    """Manages a single processing thread shared across all camera preview instances."""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.camera_context = None
            self.fps = 50
            self.current_image = None
            self.image_lock = Lock()
            self.processor_thread = None
            self.is_running = False
            self._initialized = True
    
    def start(self, camera_context, fps=50):
        """Start the shared processing thread."""
        with self.image_lock:
            self.camera_context = camera_context
            self.fps = fps
        
        if not self.is_running:
            self.is_running = True
            self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.processor_thread.start()
    
    def stop(self):
        """Stop the shared processing thread."""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=1.0)
    
    def _process_loop(self):
        """Threaded processing loop - runs once for all preview instances."""
        timestamp = time.perf_counter_ns()
        while self.is_running:
            if self.camera_context and FliSdk_V2.IsStarted(self.camera_context) and (
                    time.perf_counter_ns() - timestamp > 10 ** 9 / self.fps):
                try:
                    image_raw = np.array(FliSdk_V2.GetProcessedImageRGBANumpyArray(self.camera_context, -1))
                    #image = camera_utils.process_frame(image_raw)
                    image = image_raw
                    photo = ImageTk.PhotoImage(image=Image.fromarray(image))
                    with self.image_lock:
                        self.current_image = photo
                    timestamp = time.perf_counter_ns()
                except Exception as e:
                    print(f"Error in camera processing: {e}")
                    time.sleep(1E-2)
            else:
                time.sleep(1E-2)
    
    def get_image(self):
        """Get the latest processed image."""
        with self.image_lock:
            return self.current_image


class CameraPreview(ttk.Label):
    _processor = Processor()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.preview_image = None
    
    @classmethod
    def start_shared_processor(cls, camera_context, fps=50):
        """Start the shared processing thread (call once before creating preview instances)."""
        cls._processor.start(camera_context, fps)
    
    @classmethod
    def stop_shared_processor(cls):
        """Stop the shared processing thread."""
        cls._processor.stop()

    def display_loop(self):
        image = self._processor.get_image()
        if image:
            self.preview_image = image
            self.image = image
            self.configure(image=image)
        self.after(20, self.display_loop)

if __name__ == "__main__":
    context = FliSdk_V2.Init()
    root = tk.Tk()

    cams = camera_utils.list(context)
    camera_utils.init_camera(context, cams[0])

    CameraPreview.start_shared_processor(context, fps=50)
    preview = CameraPreview(root)
    preview.pack(fill="both", expand=True)
    preview.display_loop()
    root.mainloop()
