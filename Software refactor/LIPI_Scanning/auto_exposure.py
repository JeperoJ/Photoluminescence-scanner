
import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import FliSdk_V2 as fs
from src.camera_utils import cred3
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import time

if __name__ == "__main__":
    camera = cred3.Cred3()
    camera.connect()
    camera.configure(bias_type="Off", conversion_gain = "Medium", fps=300)

    exposures_N = 100
    exposure_min = 1/1000
    exposure_max = fs.FliCredThree.GetTintMax(camera.context)[1]
    print(exposure_max)
    exposures = np.linspace(exposure_min, exposure_max, exposures_N)
    print("Exposures range: ", exposures)

    images_N = 10
    for bias in ["Off", "Adaptive"]:
        for conv_gain in ["Low", "Medium", "High"]:
            camera.configure(bias_type=bias, conversion_gain=conv_gain)
            if bias == "Manual":
                input("Enter to build bias")
                camera.build_bias()
                input("Enter to continue")
            for exposure in exposures:
                time.sleep(0.1)
                camera.configure(exposure=exposure)
                images = camera.get_images(images_N)
                _expo_act = camera.config["exposure"]
                tifffile.imwrite(f"Auto_expo_testing//{bias}_{conv_gain}_{_expo_act}.tiff", images, photometric="minisblack", imagej=True)





# camera = cred3.Cred3()
# camera.connect()
# camera.configure(bias_type = "Adaptive", conversion_gain="High", fps=50, exposure=0.01)
# camera.start()
#
#
#
# print(camera.config["exposure"])
# image_1 = camera.frame()[1:,:]
# print(image_1.shape)
# print(image_1.max())
# print(image_1.min())
# print(image_1.dtype)
# print(np.where(image_1==image_1.max()))
# bins = np.array(range(image_1.min(), image_1.max()+1))
# plt.hist(image_1.flatten(), bins, alpha=0.5, label="Before")
# camera.auto_expose()
# image_2 = camera.frame()[1:,:]
# print(image_2.shape)
# print(image_2.max())
# print(image_2.min())
# print(image_2.dtype)
# print(np.where(image_2==image_2.max()))
# bins = np.array(range(image_2.min(), image_2.max()+1))
# plt.hist(image_2.flatten(), bins, alpha=0.5, label="After")
# plt.legend(loc="upper right")
# plt.show()
# plt.imshow(image_1)
# plt.title("Before")
# plt.show()
# plt.imshow(image_2)
# plt.title("After")
# plt.show()
