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

usr_directory = os.path.abspath(filedialog.askdirectory())
scans = [ f.path for f in os.scandir(usr_directory) if f.is_dir() ]

for scan_dir in scans:
    raw_files = glob.glob(os.path.join(scan_dir, "*.raw"))
    if len(raw_files) == 0:
        print("No raw files found in {}, skipping.".format(scan_dir))
        continue

    if len(raw_files) > 1:
        print("Multiple raw files found in {}, skipping.".format(scan_dir))
        continue

    with open(os.path.join(scan_dir, "config.toml"), "r") as f:
        config = tomlkit.load(f)

