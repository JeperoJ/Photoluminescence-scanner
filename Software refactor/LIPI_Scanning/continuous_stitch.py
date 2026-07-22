import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

import FliSdk_V2 as fs
import numpy as np
import ctypes
import matplotlib.pyplot as plt
import random
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
        self.fig = plt.imshow(np.zeros((self.height, self.width), dtype=np.int16))
        self.fps = fps
        fs.AddCallBackNewImage(context=context, func=self.wrappedFunc, fps=self.fps, beforeCopy=False, ctx=0)

    def onImageReceived(self, image, ctx):
        #width, height = fs.GetCurrentImageDimension(self.context)
        ts = time.perf_counter()
        pa = ctypes.cast(image, ctypes.POINTER(self.ArrayType))
        buffer = np.ndarray((self.height, self.width), dtype=np.int16, buffer=pa.contents)
        te = time.perf_counter()
        print(f"Array: {buffer}, ctx:{ctx}, time:{te - ts}")
        self.fig.remove()
        self.fig = plt.imshow(buffer, cmap="gray", vmin=buffer[2:-2, 2:-2].min(), vmax=buffer[2:-2, 2:-2].max())
        plt.pause(1/(2*self.fps))
        # TODO: numpy array of 16 bits image, has to be computed to a 8bit image to be displayed.

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
    #Initialization
    #stitch = np.zeros((2000, 640), dtype=np.int16)
    #buffer = rng.randint(low=2**14, dtype=np.int16, size=(300, 512, 640))
    #accumulator = rng.randint(low=2**14, dtype=np.int16, size=(300, 512, 640))

    # for image received callback
    cam = cred3.Cred3()
    cam.connect()
    cam.configure(fps=100, bias_type = "Adaptive")

    #Tests

    #Test 1
    # plt.ion()  # turning interactive mode on
    # BufferTest1(cam.context, fps=1)

    #Test 2
    BufferTest2(cam.context, fps=0, images=100)

    #Test 3
