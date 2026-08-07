import ctypes
import os
import queue
import sys
import time
import multiprocessing as mp
import tkinter as tk

fli_path = os.path.abspath(os.path.join(os.getenv("FLISDK_DIR"), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import FliSdk_V2 as fs
import numpy as np

from src.camera_utils import cred3

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - Pillow is optional
    Image = None
    ImageTk = None


fli_path = os.path.abspath(os.path.join(os.getenv("FLISDK_DIR"), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)


def _worker_loop(input_queue, result_queue, stop_event, height, width):
    array_type = ctypes.c_int16 * width * height

    while not stop_event.is_set():
        try:
            frame_ptr = input_queue.get(timeout=0.1)
            pa = ctypes.cast(frame_ptr, ctypes.POINTER(array_type))
            frame = np.ndarray((height, width), dtype=np.int16, buffer=pa.contents).copy()

            frame = frame.astype(np.float32)
            frame -= frame.min()
            frame = frame / max(frame.max(), 1.0) * 255.0
            frame = frame.astype(np.uint8)

            result_queue.put(frame)
        except queue.Empty:
            continue

class Tester:
    def __init__(self, context):
        self.height = 512
        self.width = 640
        self.ArrayType = ctypes.c_int16 * self.width * self.height

        self.ctx = context
        self._ctx = mp.get_context("spawn")
        self._stop_event = self._ctx.Event()
        self._input_queue = self._ctx.Queue(maxsize=3)
        self._result_queue = self._ctx.Queue(maxsize=3)

        self.root = tk.Tk()
        self.root.title("Camera preview")
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.photo = None

        fs.AddCallBackNewImage(context=context, func=fs.CWRAPPER(self.callback), fps=0, beforeCopy=False, ctx=0)

        self._worker = self._ctx.Process(
            target=_worker_loop,
            args=(self._input_queue, self._result_queue, self._stop_event, self.height, self.width),
            daemon=True,
        )
        self._worker.start()
        self._poll_results()

    def _poll_results(self):
        try:
            frame = self._result_queue.get_nowait()
        except Exception:
            frame = None

        if frame is not None:
            self._update_display(frame)

        if not self._stop_event.is_set():
            self.root.after(10, self._poll_results)

    def _update_display(self, frame):
        if frame is None:
            return

        if Image is not None and ImageTk is not None:
            pil_image = Image.fromarray(frame, mode="L")
            self.photo = ImageTk.PhotoImage(image=pil_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        else:
            self.canvas.delete("all")
            self.canvas.create_text(self.width // 2, self.height // 2, text="Pillow not available")

    def callback(self, image, ctx):
        if self._stop_event.is_set():
            return
        #frame = np.ndarray((self.height, self.width), dtype=np.int16, buffer=ctypes.cast(image, ctypes.POINTER(self.ArrayType)).contents).copy()
        self._input_queue.put_nowait(image)
        #print("callback")

    def close(self):
        self._stop_event.set()
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=0.2)
            if self._worker.is_alive():
                self._worker.terminate()
        try:
            self._input_queue.close()
        except Exception:
            pass
        try:
            self._result_queue.close()
        except Exception:
            pass
        if self.root is not None:
            self.root.destroy()


if __name__ == "__main__":
    cam = cred3.Cred3()
    cam.connect()
    cam.configure(fps=100, bias_type="Adaptive")
    cam.start()

    test = Tester(cam.context)
    try:
        test.root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        test.close()
        if cam._connected:
            cam.stop()
            cam.disconnect()