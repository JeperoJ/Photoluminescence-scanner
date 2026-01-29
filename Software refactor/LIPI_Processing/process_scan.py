import numpy as np
import os
import sys
import tkinter as tk
import tifffile
import src.utils.ingaas_processing as ingaas_processing
from src import stitching
import cv2
from matplotlib import pyplot as plt
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.call('wm', 'attributes', '.', '-topmost', True)

def close_program(reason = ""):
    print(f"Exiting Program due to {reason}")
    root.destroy()
    sys.exit(0)

def select_file(file_descriptor):
    root = tk.Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True)
    file_path = None
    user = input(f"Navigate to {file_descriptor} using: 1. File Selection Dialog 2.:  ")
    if user=="1":
        file_path = filedialog.askopenfilename()
    elif user=="2":
        file_path = input("Input file path: ")
    else:
        raise ValueError("Invalid user input")
    
    if file_path == None:
        raise ValueError("File path not set, but it should be by this point. Something has gone wrong.")

    root.destroy()
    return file_path

#Basic parameters
width, height = 640, 512  #C-RED 3 image dims
cal_path = None

print("Loading calibration")
user=input("Use default path?[(y)/n]: ")
if user=="y" or user=="":
    cal_path = os.path.join(os.getcwd(), "data\\calibration")
elif user=="n":
    user = input("Navigate to calibration files using: 1. File Selection Dialog 2. Manually Entering Filepath: ")
    if user=="1":
        cal_path = filedialog.askdirectory()
    elif user=="2":
        cal_path = input("Input file path: ")
    else:
        close_program("Bad Input")
else:
    close_program("Bad Input")

K=np.load(os.path.join(cal_path,"K_matrix.npy"))
P=np.load(os.path.join(cal_path,"P_matrix.npy"))
DIM=np.load(os.path.join(cal_path,"DIM_matrix.npy"))

print("Successfully loaded the calibration files")
print("Loading Image(s)")
print("Please select an image file or directory")

image_path = filedialog.askopenfilename()
images = tifffile.imread(image_path)

print("Successfully loaded the images")
speed = int(input("Gantry speed used: "))
fps = int(input("Camera fps: "))


images_undistort = ingaas_processing.undistort(images, K, P, DIM)
# plt.imshow(images_undistort[0])
# plt.show()

images_rot = [np.rot90(im, k=3) for im in images_undistort]
# plt.imshow(images_rot[0])
# plt.show()


stitched = stitching.continuous(images_rot, speed, fps)

PLimg = ingaas_processing.lin_stretch_img(stitched, 1, 99.99)
plt.imshow(PLimg, cmap="gray")
plt.show()


