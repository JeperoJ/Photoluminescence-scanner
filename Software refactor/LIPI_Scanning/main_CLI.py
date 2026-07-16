
import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

from src.scanner import scanner

import tkinter as tk
from tkinter import filedialog


root = tk.Tk()
root.withdraw()
root.call('wm', 'attributes', '.', '-topmost', True)

scan_robot = scanner.Scanner()

print("Welcome!")

#Gantry connecting
print("Setting up gantry")
#t = input("Do auto connect? (y/[n]):")
#if t == "y":
#    scan_robot.robot.connect()
#else:
available_ports = scan_robot.robot.get_ports()
print("Available ports:")
#choose between available ports
for i in range(len(available_ports)): print("port {}: {}".format(i, available_ports[i]))
t=input("Choose port (typically shows board as USB serial device): ")
port=available_ports[int(t)].device
print(port)
scan_robot.robot.connect(port)
print("Gantry connected!")

#Camera connecting
print("Setting up camera")
scan_robot.camera.connect()
print("Camera connected!")

#Config load
t=input("Press enter to load config file, or type 1 to use default")
if t == "1":
    scan_robot.configure_system()
else:
    file = filedialog.askopenfilename()
    scan_robot.load_config(file)

#Calibrate gantry
input("Calibrating gantry. Press enter when ready...")
scan_robot.robot.calibrate()
print("Gantry calibrated!")

#Camera calibration
if scan_robot.camera.config["bias_type"] == "Manual":
    input("Camera calibration. Cover camera, and press enter when ready...")
    scan_robot.camera.build_bias()

#Auto Exposure
t = input("Do auto exposure? (y/[n]):")
if t == "y":
    move = False
    t = input("Move for auto exposure? (y/[n]):")
    if t == "y":
        move = True
    input("Remove camera cover, and turn on lightbar if desired. Press enter when ready...")
    scan_robot.auto_expose(iterations=10, move=move, position=1000)
    if scan_robot.camera.config["bias_type"] == "Manual":
        input("Camera re-calibration. Cover camera, and press enter when ready...")
        scan_robot.camera.build_bias()



#Specify data path and scan
path = filedialog.askdirectory()
input("Scanner will now do setup. Please keep hands clear of gantry area. Press enter when ready...")
scan_robot.setup(path)
input("Scanner ready. Enable lightbar and remove camera cover, and keep hands clear of gantry area. Press enter when ready...")
scan_robot.scan()