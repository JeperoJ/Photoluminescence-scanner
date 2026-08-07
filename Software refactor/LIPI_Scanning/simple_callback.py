import ctypes
import os
import queue
import sys
import time
import multiprocessing as mp
import tkinter as tk
import asyncio as aio

import FliSdk_V2 as fs
import numpy as np
import matplotlib.pyplot as plt
import tifffile

from src.camera_utils import cred3

fli_path = os.path.abspath(os.path.join(os.getenv("FLISDK_DIR"), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

class CallbackHandler:
    def __init__(self, queue_out: mp.Queue):
        self.queue_out = queue_out
        self._queue = mp.Queue()

        processer = mp.Process(target=self.callback_process)
        processer.start()

    def callback(self, image, ctx):
        self._queue.put_nowait((image, ctx))

    def callback_process(self):
        while True:
            image,ctx = self._queue.get(block=True)
            self.queue_out.put(image)

def callback_loop(cb_func, rng: np.random.RandomState):
    while True:
        image = rng.randint(0, 2**14, dtype=np.int16, size=(512,640))
        cb_func(image,0)
        time.sleep(1/300)

def printer(queue: mp.Queue):
   while True:
       print(queue.get(block=True))

def displayer(queue: mp.Queue):
    fig,ax = plt.subplots()
    im = ax.imshow(queue.get(block=True))
    plt.ion()
    while True:
        im.set_data(queue.get(block=True))
        plt.pause(0.0001)

def saver(queue: mp.Queue):
    cap=300
    buffer = np.zeros((cap,512,640), dtype=np.int16)
    idx = 0

    while True:
        buffer[idx] = queue.get(block=True, timeout=3)
        idx+=1
        if idx==cap:
            break
    plt.imshow(buffer[0], cmap='gray')
    plt.show(block=True)
    print("A")
    tifffile.imwrite("test.tiff", buffer, photometric="minisblack", imagej=True)
    print("B")




if __name__ == '__main__':
    rng = np.random.RandomState(42)
    out_q = mp.Queue(maxsize=10)
    cb_handler = CallbackHandler(out_q)
    cb_producer = mp.Process(target=callback_loop, args=(cb_handler.callback,rng,))
    cb_producer.start()
    printer(out_q)
    #displayer(out_q)
    #saver(out_q)

    #cb_handler.processer.close()
    #cb_producer.close()