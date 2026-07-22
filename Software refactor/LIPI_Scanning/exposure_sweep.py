from src.camera_utils import cred3
import numpy as np
import matplotlib.pyplot as plt

camera = cred3.Cred3()
camera.connect()
camera.configure(bias_type = "Adaptive")

