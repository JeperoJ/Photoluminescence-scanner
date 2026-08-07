import threading
import time
import os
import sys

fli_path = os.path.abspath(os.path.join(os.getenv("FLISDK_DIR"), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import FliSdk_V2
import numpy as np
import multiprocessing as mp
import threading as td
import ctypes
import cv2
import concurrent.futures
import queue
from collections import deque
import scipy
from src.camera_utils import cred3
import tifffile

"""
Concept for how this should work

Camera frame -> Fast callback -> Parallel processing of frames

Fast callback:
 - Must copy the frame to prevent issues regarding scheduling fun.
    - Maybe doesnt. As long as we use the inbuilt ring buffer with approriate sizing it might be fine.
 - Primary place to diagnose issues.

"""
#
class LiveStitch:
    def __init__(self, window_size, overlap, fps, K, D, DIM):
        #Constants
        self.height = 512
        self.width = 640
        self.array_type = ctypes.c_int16 * self.width * self.height
        self.fps = fps
        self.mod_freq = 50
        self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)
        self.window_size = window_size
        self.overlap = overlap

        #Buffers and queues and pools. Essentially concurrency setup.
        # Buffer stuff is processed from for stitching.
        self.stitch_buffer_size = self.window_size + self.overlap
        self.stitch_buffer = np.zeros((self.stitch_buffer_size, self.height, self.width), dtype=np.int16)
        self.frame_numbers = np.zeros(self.stitch_buffer_size, dtype=np.int16)

        # Keeping track of everything
        self.process_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.frame_count = -self.overlap  # Increment during callback every frame that comes in, to keep track of where we are in buffers. Initted negative to get overlap frames
        self.ring_buffer_size = 3 * self.fps
        #self.pointer_queue = queue.Queue(maxsize=self.ring_buffer_size)  # No reason to keep track of more then we intend to have space for in the ring buffer
        #self.ctx = mp.get_context("spawn")
        self.pointer_queue = mp.Queue(maxsize=self.ring_buffer_size)
        self.futures = deque(maxlen=self.window_size)
        self.started = td.Event()
        self.stopped = td.Event() #Gotta be able to stop the program eventually.

        self.stitches = deque()
        self.t_dispatch = td.Thread(target=self.dispatcher)

        self.camera = cred3.Cred3()
        self.camera.connect()
        self.camera.configure(bias_type="Adaptive", fps=self.fps)
        #FliSdk_V2.SetBufferSizeInImages(self.camera.context, self.ring_buffer_size)
        # camera.add_callback(cb_func=stitcher.callback, fps=0, beforeCopy=False)
        FliSdk_V2.AddCallBackNewImage(self.camera.context, FliSdk_V2.CWRAPPER(self.callback), fps=0, beforeCopy=False, ctx=0)

        # Frame queue concept: Extra buffer layer to secure the frames from the ring buffer during callback execution.
        # Pros: Frame are now secure.
        # Cons: More memory space and time spent copying stuff around. Annoying as hell. Ugly.
        # self.frm_q_size = 10
        # self.frame_queue = np.zeros((self.frm_q_size, self.height, self.width), dtype=np.int16)

        # Buffer concept: Buffer that images can be put into, while processing is happening.
        # Pros: Processing of incoming images is uninterrupted during stiching.
        # Cons: More copying, more memory space.
        # self.buffer_size = window_size
        # self.buffer = np.zeros((self.buffer_size, self.height, self.width), dtype=np.int16)


    def callback(self, image, ctx):
        #ts = time.perf_counter()
        #pa = ctypes.cast(frame_ptr, ctypes.POINTER(self.array_type))
        #frame_idx = self.frame_count % self.frm_q_size
        #self.frame_queue[frame_idx] = np.ndarray((self.height, self.width), dtype=np.int16, buffer=pa.contents)
        #te = time.perf_counter()

        #Simplest version. Leaves casting to be a future problem. We just need to get processing eventually.
        #print("CALLBACK")
        if not self.started.is_set():
            return
        self.pointer_queue.put_nowait(0)
        #self.frame_count += 1

    def start(self):
        self.started.set()
        self.t_dispatch.start()
        self.camera.start()

    def stop(self):
        self.started.clear()
        self.stopped.set()
        self.t_dispatch.join()
        self.camera.stop()

    def get_result(self):
        return np.array(self.stitches, dtype=np.int16)

    def dispatcher(self):
        while True:
            #print("??")
            try:
                ptr = self.pointer_queue.get_nowait()
                print(ptr)
                if ptr is None:
                    time.sleep(1/(2*self.fps))
                    continue
                buf_idx = 2 % self.window_size
                if buf_idx == 0:
                    concurrent.futures.wait(self.futures, return_when=concurrent.futures.ALL_COMPLETED)
                    if self.frame_count > 0:
                        self.process_buffer()
                    self.stitch_buffer[:self.overlap] = self.stitch_buffer[-self.overlap:]
                    self.frame_numbers[:self.overlap] = self.frame_numbers[-self.overlap:]
                    self.futures.clear()
                self.futures.append(self.process_pool.submit(self.process_frame, ptr, buf_idx))
            except queue.Empty:
                print("Empty")
                if self.stopped.is_set():
                    break
        concurrent.futures.wait(self.futures, return_when=concurrent.futures.ALL_COMPLETED)
        self.process_buffer()

    def get_frame(self, ptr):
        pa = ctypes.cast(ptr, ctypes.POINTER(self.array_type))
        frame = np.ndarray((self.height, self.width), dtype=np.int16, buffer=pa.contents).copy()
        #tags = frame[0, 0:4]
        return frame

    def process_frame(self, ptr, buf_idx):
        frame = self.get_frame(ptr)
        tags = frame[0, 0:4]
        print(tags)
        self.stitch_buffer[buf_idx] = cv2.remap(frame, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        self.frame_numbers[buf_idx] = tags[0]

    def process_buffer(self):
        print(self.frame_numbers)
        test = self.frame_numbers[1:]-self.frame_numbers[:-1]
        print(test)
        if np.any(test!=1):
            raise ValueError("WE SKIPPED A FRAME ABORT MISSION RUN AWAY NOTHING WORKS AAAAAAAAAA")
        signal = self.stitch_buffer.sum()
        phase = self.get_phase(signal, self.fps, self.mod_freq)
        peaks, valleys = self.get_extrema_window(self.mod_freq, phase,self.fps,self.window_size)
        self.stitches.append(self.stitch_buffer[peaks, 123]-self.stitch_buffer[valleys, 123])

    def get_phase(self, x, f, f_s):
        '''
        Finds the phase of a given frequency in a signal, sampled at some other frequency.

        Args:
            x: The signal as a numpy array
            f: The frequency to find the phase of
            f_s: The frequency at which the signal was sampled
            debug_out: Whether to display some debug info. Matplotlib required.

        Returns:
            phase: The phase of the signal
            f_out: The closest frequency present in the FFT

        '''

        # Where is the modulation frequency in the results?
        fft_frequencies = scipy.fft.fftshift(scipy.fft.rfftfreq(len(x), d=1 / f_s))
        f_index = np.argmin(np.abs(f - fft_frequencies))
        f_out = fft_frequencies[f_index]

        # FFT of data
        yf = scipy.fft.fftshift(scipy.fft.rfft(x))

        # Get phase
        phase = np.angle(yf[f_index])
        return phase

    def get_extrema_window(self, f, phase, f_s, N):
        '''
        Estimate the extrema points of a discrete signal

        Args:
            f: Frequency of the signal component of interest
            phase: How the signal component is shifted. Should be in the range [-Pi,Pi]
            f_s: Frequency at which the signal is sampled
            start: Index at which to start return from
            end: Index at which to end return at

        Returns:
            peaks: Index of peaks as a numpy array
            valleys: Index of valleys as a numpy array

        '''
        peak_arg = -phase

        if peak_arg < 0:
            peak_arg += 2 * np.pi

        if peak_arg > 2 * np.pi:
            peak_arg -= 2 * np.pi

        valley_arg = peak_arg + np.pi

        base = np.arange(N) * 2 * np.pi
        peaks = np.round(f_s * (base + peak_arg) / (2 * np.pi * f)).astype(np.int32)
        valleys = np.round(f_s * (base + valley_arg) / (2 * np.pi * f)).astype(np.int32)

        # mask = np.all([peaks > start, peaks < end, valleys > start, valleys < end], axis=0)
        mask = np.all([peaks < N, valleys < N], axis=0)
        return peaks[mask], valleys[mask]


def load_calibration(calibration_file, flat_field=False):
    """
    Attempts to load camera calibration data from a file, saved with save_calibration. This calibration should always contain undistortion information
    gotten from the calibrate_raw function. All other future data included will initially be treated as optional, but will eventually be incldued by
    default.

    Parameters:
    - calibration_file (str/Path/File): File path for or file object containing the camera calibration data
    - TODO: flat_field (Bool): Indicates if the program should try to load calibration data for flat field correction
    Return:
    - tuple: A tuple containing all the calibration data
    """

    # TODO: Find out the error this raises if it goes wrong. Then put in a try-except around it
    loaded_data = np.load(calibration_file)
    K = loaded_data["K"]
    D = loaded_data["D"]
    DIM = loaded_data["DIM"]

    return K, D, DIM

if __name__ == '__main__':
    cal_path = "C://Users//jeppe//Desktop//Work Stuffs//GitHub//Photoluminescence-scanner//Software refactor//LIPI_Processing//data//calibration.npz"
    K,D,DIM = load_calibration(cal_path)
    stitcher = LiveStitch(300, 50, 10, K,D,DIM)
    stitcher.start()
    print("STARTED")
    time.sleep(2)
    print("STOPPING")
    stitcher.stop()
    print("STOPPED")
    result = stitcher.get_result()
    print(result)
    tifffile.imwrite("livetest.tiff", result, photometric="minisblack", imagej=True)
    print("???? DID IT WORK")


