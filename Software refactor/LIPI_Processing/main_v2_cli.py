import os
import sys
import glob
import tomlkit
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pathlib

import src.utils.scanner_processing as scp
import src.utils.ingaas_processing as ip

import tifffile

#For asking file names
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.call('wm', 'attributes', '.', '-topmost', True)

cal_path = "data/calibration.npz"

print("---Welcome to the LIPI CLI processing tool---")
print("Options:")
print(" - 1. Batch process folder")
print(" - 2. Process single scan")
t=int(input("Enter your choice: "))
print(t)
if t == 1:
    file_types = ["raw", "tiff"]
    usr_directory = os.path.abspath(filedialog.askdirectory())
    scans = [ f.path for f in os.scandir(usr_directory) if f.is_dir() ]
elif t == 2:
    filename = filedialog.askdirectory()
    scans = [filename]
else:
    raise ValueError("Invalid choice")

for scan_dir in scans:
    raw_files = glob.glob(os.path.join(scan_dir, "*.raw"))
    if len(raw_files) == 0:
        print("No raw files found in {}, skipping.".format(scan_dir))
        continue

    if len(raw_files) > 1:
        print("Multiple raw files found in {}, skipping.".format(scan_dir))
        continue

    scan_path = raw_files[0]

    with open(os.path.join(scan_dir, "config.toml"), "r") as f:
        config = tomlkit.load(f)

    #From config get:
    #FPS
    #Get or default
    #Modulation Freq (50)
    #Focal Length (6)
    #Camera Height (1045) (misspelling, check for correct and wrong)

    #FPS
    fps = config["camera"]["fps"]

    #Speed
    speed = config["robot"]["speed"]

    #Modulation Frequency
    try:
        mod_freq = config["general"]["modulation_freq"]
    except KeyError:
        mod_freq = 50
        print("Modulation frequency not configured in config.toml. Defaulting to 50")

    #Focal Length
    try:
        focal = config["general"]["focal_length"]
    except KeyError:
        focal = 6
        print("Focal length not configured in config.toml. Defaulting to 6")

    #Camera Height
    try:
        H_cam = config["robot"]["height_camera"]
    except KeyError:
        try:
            H_cam = config["robot"]["heigh_camera"]
        except KeyError:
            H_cam = 1045
            print("Camera height not configured in config.toml. Defaulting to 1045")

    print("Config loading done")

    #Load image
    #Get Extrema
    #Save all necessary images
    #SNR calcs

    print(f"Processing scan {scan_path}")
    scan = scp.load_scan(scan_path, 640, 512, cal_path=cal_path)
    index = 4000
    while True:
        plt.imshow(scan[index])
        plt.show()
        t=input("Advance? (y/[n]): ")
        if t == "y":
            index += 1
        else:
            break
    while True:
        bottom_line = int(input("Enter bottom line: "))
        top_line = int(input("Enter top line: "))
        plt.imshow(scan[index])
        plt.hlines(top_line, 0, 640, "r")
        plt.hlines(bottom_line, 0, 640, "g")
        plt.show()
        t=input("Satisfied? (y/[n]): ")
        if t == "y":
            break
    tifffile.imwrite(os.path.join(scan_dir, "scan.tif"), scan[:, bottom_line:top_line, :], photometric="minisblack", imagej=True)

    # plt.show()
    # peaks,valleys = scp.get_extrema_scan(scan, 300, 0, f_m=mod_freq, fps=fps)
    # frame_profile = scan.sum(axis=2)
    # frame_diffs = frame_profile[peaks] - frame_profile[valleys]
    # #plt.plot(np.sum(np.abs(frame_diffs), axis=0))
    # #plt.show()
    # lom = np.argmax(np.mean(np.abs(frame_diffs), axis=0))
    # print(lom)
    # plt.imshow(ip.lin_stretch_img(scan[peaks[200]]-scan[valleys[200]], 0.3, 99.7))
    # plt.hlines(lom, 0, 640, "r")
    # plt.show()
    # t = input("Overwrite LOM? (y/[n]): ")
    # if t == "y":
    #     lom = int(input("Enter LOM: "))
    # Sig1 = scan[peaks,lom,:]
    # Sig2 = scan[peaks-1,lom,:]
    # Bg = scan[valleys,lom,:]
    # stitch = Sig1-Bg
    #Save work