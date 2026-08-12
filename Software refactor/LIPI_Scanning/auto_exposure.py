
import sys
import os

from flet.controls import margin

fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import FliSdk_V2 as fs
from src.camera_utils import cred3
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import time
import scipy.optimize as opt


def get_brightness(images, x1=2, y1=2, x2=-2, y2=-2):
    """
    Calculates the brightness of an image or series of images.

    Args:
        images: Captured images
        x1, y1, x2, y2: Area to calculate brightness in

    Returns:
        brightness: float
    """

    return np.max(images[y1:y2, x1:x2])


def auto_expose(self: cred3.Cred3, target_distance, N=10, x1=2, y1=2, x2=-2, y2=-2):
    """
    Auto exposes camera using methods from numerical analysis implemented in SciPy

    Args:
        target_distance: Target distance from max pixel value (14 bit)
        N: Images to capture for each iteration
        x1, y1, x2, y2: Bounds area that is exposed for
    """
    bias_before = self.config["bias_type"]
    self.configure(bias_type="Off")

    brightness_max = 2**14-1
    res, exposure_min, exposure_max = fs.FliCredThree.GetTintRange(self.context)
    if not res:
        print("Failed to get Tint range")
        return None
    print("Exposure range: ", exposure_min, exposure_max)
    brightness_target = brightness_max - target_distance # Target Y value

    def f(x):
        self.configure(exposure=x)
        images = self.get_images(N)
        brightness = get_brightness(images, x1, y1, x2, y2)
        return brightness - brightness_target

    optimized_exposure = opt.toms748(f, exposure_min, exposure_max)

    self.configure(bias_type = bias_before, exposure = optimized_exposure)
    return None



if __name__ == "__main__":
    camera = cred3.Cred3()
    camera.connect()
    camera.configure(bias_type="Off", conversion_gain = "Medium", fps=300, exposure=1/(300*100))

    plt.imshow(camera.get_images(1)[0][2:-2,2:-2], cmap="gray")
    plt.show()

    target_distance = 1000
    images_N = 10
    auto_expose(camera, target_distance, images_N)

    plt.imshow(camera.get_images(1)[0][2:-2, 2:-2], cmap="gray")
    plt.show()



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
