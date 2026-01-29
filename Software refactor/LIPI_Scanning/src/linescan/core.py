import os
from ...src import camera_utils, gantry_utils
from ...src.camera_utils.FLI_API import FliSdk_V2

__all__ = ["continuous"]

def continuous(gcode_handler,context,savePath,frameRate,speed=5000):
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
    #bufferSize=nImages+400
    gcode_handler.set_speed([speed,speed]) #set speed for both axes
    FliSdk_V2.Stop(context)
    print(FliSdk_V2.GetBufferFilling(context), FliSdk_V2.GetImage)
    FliSdk_V2.ResetBuffer(context)

    gcode_handler.set_position(200,0)
    gcode_handler.set_position(dist_travel+100,dist_travel)
    #imageAcquisition.acquireImage(context,bufferSize,frameRate,nImages,savePath, fileName="scan")
    gcode_handler.wait()
    return None