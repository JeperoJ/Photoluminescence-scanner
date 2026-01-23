import serial.tools.list_ports
import sys
import datetime
import os
from . import gCodeHandler
from src.camera_utils import imageAcquisition

__all__ = ['get_ports', 'scan_continuous', "connect", "calibrate"]
#TODO: Make Self Contained to avoid handling gantry context outside

def get_ports():
        """
        Get a list of available serial ports.
        Returns:
            ports: A list of available serial ports.
        """
        ports = serial.tools.list_ports.comports()
        # return [port.device for port in ports]
        return ports

def connect(device):
    port = device.device
    gcode_handler = gCodeHandler.GCodeHandler(port)
    gcode_handler.connect()
    return gcode_handler

def calibrate(gcode_handler):
    """
    Calibration method for parallel X Y gantry. First, check if end stops are functional, even if they are triggered. Then, home the gantry.
    """
    #First make sure no end stops are triggered:
    try:
        endStop= ["M120", #enable end stops
            "M119", #Check end stop status
        ]
        t=gcode_handler.send_gcode(endStop)
        axis_trig = []
        count = 0  # count for error. Do not loop forever, max two times for each axis
        while any("TRIGGERED" in line for line in t) and count < 2:
            #Check end stops
            axis_trig = []
            for line in t:
                    if "TRIGGERED" in line:
                        axis = line.split("_")[0]  # Get the axis letter (X, Y, Z, etc.)
                        axis_trig.append(axis)
            print(f"End stop for axis(es) {', '.join(axis_trig)} is triggered. Attempting to move away.")
            if axis == 'x' or axis == 'x2':
                gcode_handler.send_gcode("G0 X30")
                gcode_handler.wait()
            elif axis == 'y' or axis == 'y2':
                gcode_handler.send_gcode("G0 Y30")
                gcode_handler.wait()
            else:
                raise ValueError(f"Unknown axis {axis} in end stop status.")
            t = gcode_handler.send_gcode("M119")
            count += 1
                # if "TRIGGERED" in t:
                #     raise RuntimeError(f"End stop for axis {axis} is still triggered after moving.")
    except:
        print("Error checking end stops")
        sys.exit()
    
    gcode_handler.auto_home()
    gcode_handler.wait()
    print("Gantry homed!")

def scan_continuous(gcode_handler,context,savePath,frameRate,speed=5000):
    """
    Perform a continuous scan of a PV panel using a gantry system and save the acquired images.
    Parameters:
        gcode_handler (object): The handler object for controlling the gantry system.
        context (object): FLI context object for image acquisition.
        savePath (str): path where the scanned images will be saved.
        frameRate (int): frame rate for image acquisition.
        speed (int, optional): speed of the gantry in mm/min. Default is 5000 mm/min.
    Raises:
        ValueError: If the scan is interrupted by the user.
    Notes:
    - The user is prompted to place the PV panel under the light source and remove the camera cover before starting the scan.
    - The function calculates the number of images to be acquired based on the travel distance and frame rate.
    - The function waits for the gantry to complete its movement before finishing.
    - The scanned image is saved with a timestamp in the filename.
    """
    #offsetBegin=500 #offset from the first edge of the gantry to end stops. This is the 0-point in real life
    #offsetEnd=100 #offset from the last edge of the gantry to max travel of the axes
    dist_travel=2000#(2500-offsetBegin-offsetEnd) #Distance with offset included
    nImages=int(dist_travel/(speed/60)*frameRate)
    bufferSize=nImages+400
    gcode_handler.set_speed([speed,speed]) #set speed for both axes
    gcode_handler.set_position(200,0)
    gcode_handler.set_position(dist_travel+100,dist_travel)
    imageAcquisition.acquireImage(context,bufferSize,frameRate,nImages,savePath, fileName="scan")
    gcode_handler.wait()