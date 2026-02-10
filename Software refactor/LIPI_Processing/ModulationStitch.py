import numpy as np
import os
import sys
import tkinter as tk
import tifffile
import src.utils.ingaas_processing as ingaas_processing
from src import stitching
from src.stitching import helpers
import cv2
from matplotlib import pyplot as plt
from tkinter import filedialog
import scipy
#import toml_rs as tml
import io
import manualStitch
import math

separate=True
mod_freq = 50
FPS = 300
print(f"mod_freq: {mod_freq}, FPS: {FPS}")
n_images = FPS / mod_freq  # Change this value to process different numbers of images
if n_images != int(n_images):
    raise ValueError(f"FPS must be an integer multiple of mod_freq. Current n_images: {n_images}")
n_images = int(n_images)
impath_list = []
if separate:
    im_path = filedialog.askopenfilename(title='Select images to process')
    out_path = filedialog.askdirectory(title='Select output image path')
    #images = np.array(tifffile.imread(im_path))

    impath_list = manualStitch.separateModulated(im_path, out_path, n=n_images)
else:
    for i in range(n_images):
        im_path = filedialog.askopenfilename(title=f'Select image {i+1} to process')
        impath_list.append(im_path)
    out_path = filedialog.askdirectory(title='Select output image path')

cwd=os.getcwd()

calpath=os.path.join(cwd,"data/calibration")
print(calpath)

################
#User variables:
################
#path=os.path.join(impath,"scan_cont_2025-02-24_15-53.tiff")
# path1=os.path.join(impath,"scan_cont_2025-02-28_15-48_10ms_low_w_IR.tiff")
# path2=os.path.join(impath,"scan_cont_2025-02-28_15-51_10ms_1_3A_low_noIR_outdoor.tiff")
#path="C:/Users/carle/OneDrive - Danmarks Tekniske Universitet/THESIS/Work Files/Camera/Images/scan_cont_2025-02-24_15-53.tiff"
#rotation=180+88 #In degrees
rotation=90
speed=5000
#Speed in different axes, given v^2=vx^2+vy^2 and v1/v2=px/py
offset=200
p1=2100-offset
p2=2000
speedx=p1*speed/(math.sqrt(p1**2+p2**2))
speedy=p2*speed/(math.sqrt(p1**2+p2**2))
speedx=4000


#drift=0.02448 #new drift factor (for the 100mm offset in set_position(end+100,end))
#drift=0.0466 #old drift factor (without 100mm offset)
drift=0.05622 #new new experimental drift factor


###################
#Function selection
###################

#Run either manualstitch or savevideo or subtract. Comment out the other two.
#out_path = filedialog.askdirectory(title='Select Stitched Image Save path')

PLimg_list = []
for path in impath_list:
    
    PLimg = manualStitch.manualstitch(path,calpath,rotation,speedx,drift,FPS)
    PLimg_list.append(PLimg)
# modulated_img = PLimg_list[2]-PLimg_list[0][:,:-1]
# cv2.imshow("testmodulation",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
# cv2.waitKey(0)

# modulated_img = PLimg_list[2]-PLimg_list[1]
# cv2.imshow("testmodulation",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# modulated_img = PLimg_list[0][:,:-1]-PLimg_list[1]
# cv2.imshow("testmodulation",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
# cv2.waitKey(0)
# modulated_img = PLimg_list[0][:,:-1]-PLimg_list[2]
# cv2.imshow("testmodulation",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
# cv2.waitKey(0)
# modulated_img = PLimg_list[1]-PLimg_list[0]
# cv2.imshow("testmodulation",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
# cv2.waitKey(0)

modulated_img = PLimg_list[2]-PLimg_list[4]
cv2.imshow("testmodulation",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
cv2.waitKey(0)
cropped_modulated_img = ingaas_processing.crop_image(modulated_img)
cv2.imwrite(os.path.join(out_path, "stitched_image_modulated.png"), ingaas_processing.lin_stretch_img(cropped_modulated_img, 1, 99.99))