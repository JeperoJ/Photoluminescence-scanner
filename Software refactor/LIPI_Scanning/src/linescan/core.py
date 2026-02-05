import os
from .. import camera_utils, gantry_utils
import FliSdk_V2
import math
import datetime

__all__ = ["continuous"]

def continuous(gcode_handler,context,savePath,frameRate,speed=5000,gantry_lengthx=2100,gantry_lengthy=2000):
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
    offsetBegin=200 #offset from the first edge of the gantry to end stops.
    px=gantry_lengthx-offsetBegin #Effective length of gantry in the X direction
    py=gantry_lengthy #Fixed length of gantry in the Y direction
    speedx=px*speed/(math.sqrt(px**2+py**2)) #Calculate speed in the X direction
    speedy=py*speed/(math.sqrt(px**2+py**2)) #Calculate speed in the Y direction
    speedtest=speed/(math.sqrt(2))
    nImages=int(px/(speedx/60)*frameRate)
    bufferSize=nImages+200
    bufferSize=1000
    gcode_handler.set_speed(speedtest) #set speed for both axes
    gcode_handler.set_position(offsetBegin,0) #Set offset (to see panel before the light bar)
    gcode_handler.set_position(gantry_lengthx,gantry_lengthx-offsetBegin)
    image_start = FliSdk_V2.GetBufferFilling(context)
    gcode_handler.wait()
    image_end = FliSdk_V2.GetBufferFilling(context)
    fileName=f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.raw"
    file_path=os.path.join(savePath,fileName)
    FliSdk_V2.SaveBuffer(context,file_path,image_start,image_end)
