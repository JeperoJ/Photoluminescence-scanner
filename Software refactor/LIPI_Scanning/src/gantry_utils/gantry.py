import serial
import time
import serial.tools.list_ports
import sys
import math
import os
from . import gCodeHandler

#gantry_lengthx=2100, gantry_lengthy=2000
#width_x, width_y
#, speed=5000

#Settings
#Dimensions
#Speed

class Gantry():
    def __init__(self):
        self.handler = None
        self.connected = False
        self.configured = False
        self.calibrated = False

        self.config = {}
        self._config_default = {
            "length_upper" : 2100,
            "width_upper": 0,
            "height_upper": 0,
            "length_lower" : 2000,
            "width_lower" : 0,
            "height_lower" : 0,
            "speed" : 5000,
            "lightbar_angle": 30,
            "lightbar_height": 0,
            "heigh_camera": 1045
        }
    def close(self):
        if self.connected:
            self.handler.disconnect()

    def __del__(self):
        self.close()


    def get_ports(self):
        """
        Get a list of available serial ports.
        Returns:
            ports: A list of available serial ports.
        """
        ports = serial.tools.list_ports.comports()
        # return [port.device for port in ports]
        return ports


    def connect(self, device=None):
        if device is None:
            ports = self.get_ports()
            device = ports[[port.serial_number for port in ports].index("0400D018AF3D08A05C82F1D8F50020C0")].device #Makes list of serial numbers, gets the index of the correct serial number, selects the corresponding port, finally gets that device
        gcode_handler = gCodeHandler.GCodeHandler(device)
        gcode_handler.connect()
        self.handler = gcode_handler
        self.connected = True

    def configure(self, config_dict=None, **settings):
        if not self.connected:
            raise ValueError("Class instance not connected to the gantry. Run connect function first.")

        if config_dict is None:
            config_dict = settings

        if not self.configured:
            config_dict = self._config_default | config_dict #Python always select elements from second dictionary. This means that any keyword in both will always have the user value, and any only in default the default value

        for key,value in config_dict.items():
            print(key)
            if key not in self._config_default:
                raise ValueError(f"Invalid setting {key}. Valid settings are {self._config_default.keys()}")
            if key == "speed":
                self.handler.set_speed(value*math.sqrt(2))
            self.config[key] = value

        self.configured = True

    def calibrate(self, timeout=None):
        """
        Calibration method for parallel X Y gantry. First, check if end stops are functional, even if they are triggered. Then, home the gantry.
        """
        # First make sure no end stops are triggered:
        endStop = ["M120",  # enable end stops
                   "M119",  # Check end stop status
                   ]
        t = self.handler.send_gcode(endStop)
        axis_trig = []
        count = 0  # count for error. Do not loop forever, max two times for each axis
        while any("TRIGGERED" in line for line in t) and count < 2:
            # Check end stops
            axis_trig = []
            for line in t:
                if "TRIGGERED" in line:
                    axis = line.split("_")[0]  # Get the axis letter (X, Y, Z, etc.)
                    axis_trig.append(axis)
            print(f"End stop for axis(es) {', '.join(axis_trig)} is triggered. Attempting to move away.")
            if axis == 'x' or axis == 'x2':
                self.handler.send_gcode("G0 X30")
                self.handler.wait(timeout=10)
            elif axis == 'y' or axis == 'y2':
                self.handler.send_gcode("G0 Y30")
                self.handler.wait(timeout=10)
            else:
                raise ValueError(f"Unknown axis {axis} in end stop status.")
            t = self.handler.send_gcode("M119")
            count += 1
            # if "TRIGGERED" in t:
            #     raise RuntimeError(f"End stop for axis {axis} is still triggered after moving.")

        self.handler.auto_home()
        self.handler.wait(timeout=timeout)
        print("Gantry homed!")