import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import asyncio

import FliSdk_V2 as fs
import numpy as np
import ctypes
import matplotlib.pyplot as plt
import random
import queue
import threading
import time
import tifffile

from src.scanner import scanner
from src.camera_utils import cred3

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()
root.call('wm', 'attributes', '.', '-topmost', True)

class BufferTest1:
    def __init__(self, context, fps):
        self.wrappedFunc = fs.CWRAPPER(self.onImageReceived)
        self.height = 512
        self.width = 640
        self.ArrayType = ctypes.c_int16 * self.width * self.height
        self.fps = fps
        self._stop_event = threading.Event()
        self._latest_frame = None
        self._frame_count = 0
        self.fig = None
        self.ax = None
        self.image = None
        self._frame_queue = queue.Queue(maxsize=1)

        plt.ion()
        fs.AddCallBackNewImage(context=context, func=self.wrappedFunc, fps=25, beforeCopy=False, ctx=0)

    def onImageReceived(self, image, ctx):
        if self._stop_event.is_set():
            return

        ts = time.perf_counter()
        pa = ctypes.cast(image, ctypes.POINTER(self.ArrayType))
        buffer = np.ndarray((self.height, self.width), dtype=np.int16, buffer=pa.contents)
        te = time.perf_counter()
        self._latest_frame = buffer
        self._frame_count += 1

        try:
            self._frame_queue.get_nowait()
        except queue.Empty:
            pass
        self._frame_queue.put_nowait(buffer)
        #print(f"Received frame {self._frame_count}, ctx:{ctx}, time:{te - ts}")

    def _display_frame(self, frame):
        if self.image is None:
            self.fig, self.ax = plt.subplots()
            self.image = self.ax.imshow(frame, cmap="gray")
            self.ax.set_title("Camera preview")
            self.ax.set_axis_off()
        else:
            self.image.set_data(frame)
            vmin = frame[2:-2, 2:-2].min()
            vmax = frame[2:-2, 2:-2].max()
            #if np.isfinite(vmin) and np.isfinite(vmax):
            self.image.set_clim(vmin, vmax)

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def run(self):
        self.fig, self.ax = plt.subplots()
        self.image = self.ax.imshow(np.zeros((self.height, self.width), dtype=np.uint16), cmap="gray")
        self.ax.set_title("Camera preview")
        self.ax.set_axis_off()
        plt.show(block=False)

        while not self._stop_event.is_set():
            try:
                frame = self._frame_queue.get_nowait()
            except queue.Empty:
                plt.pause(0.001)
                continue

            self._display_frame(frame)
            plt.pause(0.001)

    def stop(self):
        self._stop_event.set()
        if self.fig is not None:
            plt.close(self.fig)

class BufferTest2:
    def __init__(self, context, fps, images):
        self.wrappedFunc = fs.CWRAPPER(self.onImageReceived)
        self.height = 512
        self.width = 640
        self.ArrayType = ctypes.c_int16 * self.width * self.height
        self.fps = fps
        fs.AddCallBackNewImage(context=context, func=self.wrappedFunc, fps=self.fps, beforeCopy=False, ctx=0)

        self.images = images
        self.buffer = np.zeros((self.images, self.height, self.width), dtype=np.int16)
        self.idx = 0

    def onImageReceived(self, image_ptr, ctx):
        # width, height = fs.GetCurrentImageDimension(self.context)
        pa = ctypes.cast(image_ptr, ctypes.POINTER(self.ArrayType))
        image = np.ndarray((self.height, self.width), dtype=np.int16, buffer=pa.contents)
        self.buffer[self.idx] = image
        self.idx += 1
        if self.idx == self.images:
            tifffile.imwrite('temp.tif', self.buffer, photometric='minisblack')
            exit()
        # TODO: numpy array of 16 bits image, has to be computed to a 8bit image to be displayed.

class BufferTest3:
    def __init__(self, context, fps, images):
        pass

if __name__ == "__main__":
    cam = cred3.Cred3()
    test = None

    try:
        cam.connect()
        cam.configure(fps=100, bias_type="Off")

        test = BufferTest1(cam.context, fps=0)
        cam.start()
        print("Waiting for camera callbacks. Press Ctrl+C to stop.")
        test.run()
    except KeyboardInterrupt:
        print("Stopping camera stream...")
    finally:
        if test is not None:
            test.stop()
        if cam._connected:
            cam.stop()
            cam.disconnect()

    #Test 2
    #BufferTest2(cam.context, fps=0, images=100)

    #Test 3
