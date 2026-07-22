import cv2
from src.utils import ingaas_processing as ip
from src.utils import scanner_processing as scp
import numpy as np
import matplotlib.pyplot as plt
import time
from pathlib import Path
from multiprocessing import Pool
import functools
from joblib import Parallel, delayed
from src.utils import ingaas_processing as ip
#from src.utils import scanner_processing as scp
import os

def chunked_loader(file_path, cal_path, chunk_img=1000, chunks=-1, width=640, height=512):
    K, P, DIM = ip.load_calibration(cal_path)
    images = np.array([])
    with open(file_path, "rb") as f:
        while True:
            buffer = f.read(2*chunk_img*width*height)
            if not buffer:
                break
            subset=np.frombuffer(buffer, dtype=np.int16).reshape((chunk_img,height,width))
            images= np.append(images, ip.undistort(subset, K, P, DIM))
            chunks -= 1
            if chunks == 0:
                break
    return np.array(images)

def chunked_loader_v2(file_path, cal_path, chunk_img=1000, chunks=-1, width=640, height=512):
    K, P, DIM = ip.load_calibration(cal_path)
    N_imgs = int(os.path.getsize(file_path)/(2*width*height))
    images = np.zeros((N_imgs, height, width), dtype=np.int16)
    idx_s = 0
    while True:
        idx_e = idx_s+chunk_img
        if idx_e > N_imgs:
            idx_e = N_imgs
        images[idx_s:idx_e] = ip.undistort(ip.load_raw_image(file_path, images=idx_e-idx_s, offset_images=idx_s), K, P, DIM)
        idx_s += chunk_img
        if idx_s >= N_imgs:
            break
        chunks -= 1
        if chunks == 0:
            break
    return images

# def para_processor(file_path, cal_path, width=640, height=512):
#     K, P, DIM = ip.load_calibration(cal_path)
#     img_size = 2*width*height
#     N_imgs = int(os.path.getsize(file_path) / img_size)
#     map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, P, np.eye(3), K, DIM, cv2.CV_16SC2)
#     #undistorted_imgs = Parallel(n_jobs=-1, backend="threading")(delayed(cv2.remap)(np.frombuffer(f.read(img_size), dtype=np.int16).reshape(height,width), map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) for i in range(N_imgs))
#     undistorted_imgs = np.array(Parallel(n_jobs=2000, backend="threading")(
#         delayed(cv2.remap)(np.fromfile(file_path, dtype=np.int16, count=int(img_size/2), sep="", offset=img_size*i).reshape(height, width), map1, map2,
#                            interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) for i in range(N_imgs)))
#     return undistorted_imgs

#Functions under test
def display(image, title):
    plt.imshow(image, cmap='gray', vmin=image[1:].min(), vmax=image[1:].max())
    plt.title(title)
    plt.show()

if __name__ == "__main__":
    path = Path("C://Users//jeppe//Desktop//Work Stuffs//Data Sets//Scans//20260618_125959")
    file = list(path.glob("*.raw"))[0]
    #imgs_full = ip.load_raw_image(file, images=1001, offset_images=4000)
    #display(imgs[10], "Raw Image")
    cal_path = "data//calibration.npz"
    K, P, DIM = ip.load_calibration(cal_path)

    #Benchmark: Load and undistort a full raw
    rng = np.random.RandomState(42)
    samples = rng.randint(100, 10000, 3)
    print(samples)

    ts = time.perf_counter()
    images_v2 = chunked_loader_v2(file, cal_path, chunk_img=2000)[samples]
    te = time.perf_counter()
    print(f"Scans loaded in {te-ts} seconds using chunked v2")



