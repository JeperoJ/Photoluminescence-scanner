
import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
from src.camera_utils import cred3
import matplotlib.pyplot as plt
import numpy as np

camera = cred3.Cred3()
camera.connect()
camera.configure(bias_type = "Adaptive")

print(camera.config["exposure"])
image_1 = camera.frame()
bins = np.array(range(image_1.min(), image_1.max()+1))
plt.hist(image_1.flatten(), bins, alpha=0.5, label="Before")
camera.auto_expose()
image_2 = camera.frame()
bins = np.array(range(image_2.min(), image_2.max()+1))
plt.hist(image_2.flatten(), bins, alpha=0.5, label="After")
plt.legend(loc="upper right")
plt.show()
plt.imshow(image_1)
plt.title("Before")
plt.show()
plt.imshow(image_2)
plt.title("After")
plt.show()
