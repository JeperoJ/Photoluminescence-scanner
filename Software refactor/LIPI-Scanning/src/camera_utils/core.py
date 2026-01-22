from .FLI_API import FliSdk_V2
import os
import sys
import cv2
import time
import logging
from . import imageAcquisition
from . import helpers

#logger = logging.getLogger(__name__)

#TODO: Potentially clean things up by making a Camera class, with an interally handled context

__all__ = ['calibrate_camera', "init_camera", "disconnect", "list"]

def list(context):
    grabbers = FliSdk_V2.DetectGrabbers(context)
    for s in grabbers:
        print(f"- {s}")
    return FliSdk_V2.DetectCameras(context)

def calibrate_camera(context, adaptiveBias=False):
    # Set bad pixel correction
    helpers.PixelCorrect(context, True)

    # Buidling bias correction. Choose between NUC calibrated bias and FLI's adaptive bias (only C-RED3?)
    helpers.BuildNUCBias(context)
    if adaptiveBias:
        imageAcquisition.EnableAdaptBias(context)
        
    #TODO: Flat correction. Fixing non-uniformity response of pixels [OPTIONAL]
    #https://andor.oxinst.com/learning/view/article/how-to-use-the-hdr-mode
    # val=input("Do flat correction?[y/n]")
    # if val=="y":

    #Enable anti-blooming
    FliSdk_V2.FliCredThree.EnableAntiBlooming(context, True)
    print("Anti-blooming enabled")
    #Enable auto clip. Only after starting acquisition?????
    FliSdk_V2.ImageProcessing.EnableAutoClip(context, -1, True)
    print("Auto clip enabled")
    # Debugging display
    return context

def init_camera(context, frameRate, tintVal,camera, gain="Medium"):
    """
    Initialize the FLI camera.

    Parameters:
    context (object): The FLI SDK context.
    frameRate (float): The desired frame rate for the camera.
    tintVal (float): The desired exposure time (tint) for the camera in milliseconds.
    conversionGain (str): The desired conversion gain for the camera. Allowed values are "low", "medium", "high".

    Returns:
    None
    """
    
    ok = FliSdk_V2.SetCamera(context, camera)
    if not ok:
        print("Error while setting camera.")
        exit()

    print("Setting mode full.")
    FliSdk_V2.SetMode(context, FliSdk_V2.Mode.Full)
    print("Updating...")
    ok = FliSdk_V2.Update(context)

    if not ok:
        print("Error while updating SDK.")
        exit()

    print("Mode set to full.")

    fps = 0

    if FliSdk_V2.IsSerialCamera(context):
        res, fps = FliSdk_V2.FliSerialCamera.GetFps(context)
    elif FliSdk_V2.IsCblueSfnc(context):
        res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)
    print("Previous camera FPS: " + str(fps))

    val = frameRate
    helpers.set_fps(context,val)

    if FliSdk_V2.IsSerialCamera(context):
        res, fps = FliSdk_V2.FliSerialCamera.GetFps(context)
    elif FliSdk_V2.IsCblueSfnc(context):
        res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)

    print("New FPS read: " + str(fps))

    if FliSdk_V2.IsCredTwo(context) or FliSdk_V2.IsCredThree(context) or FliSdk_V2.IsCredTwoLite(context):
        res, response = FliSdk_V2.FliSerialCamera.SendCommand(
            context, "mintint raw")
        minTint = float(response)

        res, response = FliSdk_V2.FliSerialCamera.SendCommand(
            context, "maxtint raw")
        maxTint = float(response)

        res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "tint raw")

        print("Previous camera tint: " + str(float(response)*1000) + "ms")

        # val = input("Tint to set? (between " + str(minTint*1000) +
        #            "ms and " + str(maxTint*1000) + "ms) ")
        val = tintVal
        try:
            valFloat = float(val)
            res, response = FliSdk_V2.FliSerialCamera.SendCommand(
                context, "set tint " + str(valFloat/1000))
        except:
            print("Value is not a float")

        res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "tint raw")
        print("Current new camera tint: " + str(float(response)*1000) + "ms")
    elif FliSdk_V2.IsCblueSfnc(context):
        res, tint = FliSdk_V2.FliCblueSfnc.GetExposureTime(context)
        print("Current new camera tint: " + str(tint/1000) + "ms")

    res,conversionGain=FliSdk_V2.FliCredThree.GetConversionGain(context)
    print("Previous conversion gain: " + str(conversionGain))
    helpers.setConversionGain(context,gain)

def disconnect(context):
    """
    Stops camera context using FLI API
    """
    FliSdk_V2.Stop(context)
    FliSdk_V2.Exit(context)
    print("Camera disconnected")

# def start_context():
#     return FliSdk_V2.Init()