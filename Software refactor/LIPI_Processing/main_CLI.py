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

    #Getting scaling factor
    # dpf = speed / 60 / fps  # distance per frame (mm)
    # # dist_travel/cameraHeight=d/f
    # #doffset = 200 / H_cam * f  # distance in mm on image plane
    # dpf_f = dpf / H_cam * focal  # distance per frame in mm on image plane
    # pxratiox = 15  # um/px in x dir
    # pxratioy = pxratiox  # um/px in y dir -
    # #doffsetpx = doffset / (pxratiox / 1000)  # distance in px on image plane
    # dpf_px = dpf_f / (pxratiox / 1000)  # distance per frame in px on image plane

    #Load image
    #Get Extrema
    #Save all necessary images
    #SNR calcs

    print(f"Processing scan {scan_path}")
    scan = scp.load_scan(scan_path, 640, 512, crop_rows=(150,300), cal_path=cal_path)
    #plt.imshow(scan[4000])
    #plt.show()
    peaks,valleys = scp.get_extrema_scan(scan, 300, 0, f_m=mod_freq, fps=fps)
    frame_profile = scan.sum(axis=2)
    frame_diffs = frame_profile[peaks] - frame_profile[valleys]
    #plt.plot(np.sum(np.abs(frame_diffs), axis=0))
    #plt.show()
    lom = np.argmax(np.mean(np.abs(frame_diffs), axis=0))
    print(lom)
    plt.imshow(ip.lin_stretch_img(scan[peaks[200]]-scan[valleys[200]], 0.3, 99.7))
    plt.hlines(lom, 0, 640, "r")
    plt.show()
    t = input("Overwrite LOM? (y/[n]): ")
    if t == "y":
        lom = int(input("Enter LOM: "))
    Sig1 = scan[peaks,lom,:]
    Sig2 = scan[peaks-1,lom,:]
    Bg = scan[valleys,lom,:]
    stitch = Sig1-Bg
    #Save work

    #SNR full
    SNR, profile = scp.SNR50(Sig1, Sig2, Bg, dB=False, profile=True)
    print(stitch.shape)
    SNR_test_full = np.mean(stitch[:,100:540])/np.std(stitch[:,0:75], ddof=1)
    print(f"SNR: {SNR}, SNRNew: {SNR_test_full}")
    np.savetxt(os.path.join(scan_dir, "SNR_profile.csv"), profile, delimiter=",")
    with open(os.path.join(scan_dir, "SNR.txt"), "w") as f:
        print(f"SNR50: {SNR}", file=f)
        print(f"SNR50_test_full: {SNR_test_full}", file=f)
    plt.plot(profile)
    plt.savefig(os.path.join(scan_dir, "SNR_profile.png"))
    plt.close()

    #Images full
    def saver(x, name):
        plt.imsave(os.path.join(scan_dir, f"{name}.png"), x, cmap="gray", vmin=np.min(x), vmax=np.max(x)) #Pretty image
        np.savetxt(os.path.join(scan_dir, f"{name}.csv"), x, delimiter=",") #Usable data

    saver(Sig1, "Sig1")
    saver(Sig2, "Sig2")
    saver(Bg, "Bg")
    saver(stitch, "stitch")

    #Resizing images, SNR, and saving again
    #print(f"Resizing factor: {dpf_px}")
    resize = lambda x: cv2.resize(x, (x.shape[1], 766))
    Sig1_resize = resize(Sig1)
    Sig2_resize = resize(Sig2)
    Bg_resize = resize(Bg)
    stitch_resize = resize(stitch)

    SNR_resize, profile_resize = scp.SNR50(Sig1_resize, Sig2_resize, Bg_resize, dB=False, profile=True)
    SNR_test_resize = np.mean(stitch_resize[:, 100:540]) / np.std(stitch_resize[:, 0:75], ddof=1)
    print(f"SNR50_resize: {SNR_resize}, SNRNew_resize: {SNR_test_resize}")
    np.savetxt(os.path.join(scan_dir, "SNR_resize_profile.csv"), profile_resize, delimiter=",")
    with open(os.path.join(scan_dir, "SNR_resize.txt"), "w") as f:
        print(f"SNR50: {SNR_resize}", file=f)
        print(f"SNR50_test_resize: {SNR_test_resize}", file=f)
    plt.plot(profile_resize)
    plt.savefig(os.path.join(scan_dir, "SNR_resize_profile.png"))
    plt.close()

    saver(Sig1_resize, "Sig1_resize")
    saver(Sig2_resize, "Sig2_resize")
    saver(Bg_resize, "Bg_resize")
    saver(stitch_resize, "stitch_resize")

    #Lin strectch all images
    Sig1_process = ip.lin_stretch_img(Sig1_resize, 0.3, 99.7)
    Sig2_process = ip.lin_stretch_img(Sig2_resize, 0.3, 99.7)
    Bg_process = ip.lin_stretch_img(Bg_resize, 0.3, 99.7)
    stitch_process = ip.lin_stretch_img(stitch_resize, 0.3, 99.7)

    saver(Sig1_process, "Sig1_process")
    saver(Sig2_process, "Sig2_process")
    saver(Bg_process, "Bg_process")
    saver(stitch_process, "stitch_process")
