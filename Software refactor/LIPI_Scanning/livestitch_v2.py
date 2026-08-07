import os
import sys
import queue
import threading
import time
import ctypes
import numpy as np
import tifffile
import cv2
import FliSdk_V2
import concurrent.futures
import scipy
import collections

fli_path = os.path.abspath(os.path.join(os.getenv("FLISDK_DIR"), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

from src.camera_utils import cred3


class CallbackCollector:
    def __init__(self, window_size, overlap, K, D, DIM, fps, worker_threads, queue_size):
        # Variables
        self.height = 512
        self.width = 640
        self.ArrayType = ctypes.c_int16 * self.width * self.height
        self.fps = fps
        self.frame_count = 0
        self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)

        self.queue_size = queue_size
        self.ptr_queue = queue.Queue(maxsize=queue_size) #Pointers put here, pulled by consumer

        self.stitches = collections.deque()
        self.tags = collections.deque()

        """
        Buffers:
         - Storage buffer: Worker threads pull the data from the camera ring buffer, into here. This is only as long as
                           the processing window, because that is the information changed in each processing step.
        """
        self.window_size = window_size
        self.overlap = overlap
        self.work_buffer_size = self.window_size + self.overlap
        self.storage_buffer = np.zeros((self.window_size, self.height, self.width), dtype=np.int16) #Frames are stored here when pulled from ring buffer
        self.work_buffer = np.zeros((self.work_buffer_size, self.height, self.width), dtype=np.int16) #Copied her for processing and shuffling, to keep other threads working
        self.frame_tags = np.zeros((self.work_buffer_size, 4), dtype=np.int16)

        # Program synchronization
        self.started = threading.Event() # Makes sure we are not filling our buffers with junk (Pretty sure the camera callbacks even when the Sdk is stopped)
        self.stopped = threading.Event() # Kills the program gracefully. Each thread is shut down in turn, making sure all is processed.

        # Buffer access synchronization
        self.buffer_check = threading.Lock() # For synchronizing the threads checking the lock
        self.work_buffer_access = threading.Condition() # For locking out buffer access during copy

        self.buffer_thread = threading.Thread(target=self.process_buffer, daemon=True)
        self.buffer_thread.start()

        self.locks = [threading.Lock() for _ in range(worker_threads)]
        self.threads = [threading.Thread(target=self.consumer, args=(lock,), daemon=True) for lock in self.locks]
        for thread in self.threads:
            thread.start()


    def start(self):
        self.stopped.clear()
        self.started.set()

    def stop(self):
        self.started.clear()
        self.stopped.set()

    def finish(self):
        self.stopped.wait()
        self.buffer_thread.join()
        for thread in self.threads:
            thread.join()
        return np.array(self.stitches, dtype=np.int16), np.array(self.frame_tags, dtype=np.int16)

    def callback(self, ptr, ctx):
        if not self.started.is_set():
            return
        #ts = time.perf_counter()
        try:
            self.ptr_queue.put_nowait((ptr, self.frame_count))
        except queue.Full:
            print("Queue Full!!!")
        #print(f"Callback #{self.frame_count} received (ctx={ctx}), running in {threading.get_native_id()}")
        self.frame_count += 1
        if self.frame_count == 1200:
            self.stop()
        #te = time.perf_counter()
        #print(te-ts)

    def consumer(self, priv_lock):
        """
        Purpose: Thread function, runs continuously with the program and processed the incoming frames.

        Control flow:
        Loads data from queue
        Acquires lock for checking if buffer is full. This ensures a thread acquiring the next queue item does not accidentally process that and overwrite data
            - Checks if we have looped on the buffer
            - If so:
                - Wait for all threads to have finished the processing up to this point
                - Acquire access to the buffer work is done on
                - Copy the storage buffer in
                - Release access to the buffer
                - Notify processing thread it is ready
            - Release the lock (Implicit in context manager)
        Acquires private lock
        Does work
        Releases private lock
        """
        while True:
            try:
                ptr, frame_count = self.ptr_queue.get(block=True, timeout=1)
                buf_idx = frame_count % self.window_size
                pa = ctypes.cast(ptr, ctypes.POINTER(self.ArrayType))
                with self.buffer_check:
                    if buf_idx == 0:
                        if frame_count > 0:
                            for _lock in self.locks: # Wait for all threads to finish current work
                                _lock.acquire()
                            self.work_buffer_access.acquire() # Wait for access to buffer process. Important if we are still working on previous stitch call.
                            self.work_buffer[self.overlap:] = self.storage_buffer # Copy data into the working buffer
                            self.work_buffer_access.release()  # Relinquish access to the storage buffer
                            self.work_buffer_access.notify() # Tell stitching thread to start working
                            for _lock in self.locks:
                                _lock.release()
                        else:
                            pass
                priv_lock.acquire() # Make sure this is finished before any buffer copying occurs
                buffer = np.ndarray((self.height, self.width), dtype=np.int16, buffer=pa.contents)
                tags = buffer[0, 0:4]
                self.tags.append(tags)
                self.storage_buffer[buf_idx] = cv2.remap(buffer, self.map1, self.map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
                priv_lock.release() # Work done, release
            except queue.Empty:
                if self.stopped.is_set():
                    break

    def process_buffer(self):
        self.work_buffer_access.acquire() #Initilization shenanigans. Can only wait on a condition if underlying lock is owned.
        while True:
            self.work_buffer_access.wait() #Relinquishes lock on call, and waits for a notify call to attempt to acquire again.

            #Do work
            signal = self.work_buffer.sum() #Modulation signal
            phase = get_phase(signal, f=50, f_s=self.fps) #Phase
            peaks, valleys = get_extrema_window(50, phase, self.fps, self.window_size) #Extrema (This and above could be combined to one. Will be replaced though)
            self.stitches.append(self.work_buffer[peaks]-self.work_buffer[valleys])
            self.work_buffer[:self.overlap] = self.work_buffer[-self.overlap:]
            if self.stopped.is_set():
                break

def get_phase(x, f, f_s):
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

def get_extrema_window(f, phase, f_s, N):
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

if __name__ == "__main__":
    # Variables
    buffer_seconds = 3
    fps_target = 605
    workers = 10

    window_size = 250
    overlap = 50

    #Setup
    cal_path = "C://Users//jeppe//Desktop//Work Stuffs//GitHub//Photoluminescence-scanner//Software refactor//LIPI_Processing//data//calibration.npz"
    K, D, DIM = load_calibration(cal_path)
    cam = cred3.Cred3()
    cam.connect()
    cam.configure(bias_type="Adaptive", fps=fps_target)
    fps = cam.config["fps"]
    ring_buffer_size = int(buffer_seconds*fps)
    queue_size = int((buffer_seconds-1)*fps) # 1 second gap between the size of the ring buffer and the queue, just for security
    FliSdk_V2.SetBufferSizeInImages(cam.context, ring_buffer_size)
    collector = CallbackCollector(window_size=window_size, overlap=overlap, K=K, D=D, DIM=DIM, fps=cam.config["fps"], worker_threads=workers, queue_size=queue_size)
    cam.add_callback(collector.callback, 0, False)
    cam.start()
    collector.start()
    result, tags = collector.finish()
    print(result.shape)
    print(tags)
    #tifffile.imwrite("livetest.tiff", collector.work_buffer, photometric="minisblack", imagej=True)
    #thread.join()

    #collector.stop()

    #thread.join(timeout=5)

    #print(f"Collected {collector.que.qsize()} callback entries:")
    #while not collector.que.empty():
    #    print(collector.que.get_nowait())
