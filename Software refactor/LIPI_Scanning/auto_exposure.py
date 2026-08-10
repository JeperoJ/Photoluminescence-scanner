
import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import FliSdk_V2
#from src.camera_utils import cred3
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import time
def setFPS(context,val):
    try:
        valFloat = float(val)
        if FliSdk_V2.IsSerialCamera(context):
            FliSdk_V2.FliSerialCamera.SetFps(context, valFloat)
        elif FliSdk_V2.IsCblueSfnc(context):
            FliSdk_V2.FliCblueSfnc.SetAcquisitionFrameRate(context, valFloat)
    except:
        print("Value is not a float")
def BuildNUCBias(context):
    """
    Build NUC Bias for FLI C-RED 3.

    Parameters:
    context (object): The FLI SDK context.

    Returns:
    None
    """
    print("NUC Bias correction for FLI C-RED 3 started.....") 
    nImages=256
    #nImages=input("How many images to use? (default 256)")
    print("[DEBUGGING]getting current bias state")
    res,state= FliSdk_V2.FliCred.GetBiasState(context)
    if state:
        #Change bias to false to generate new bias. Not sure if necessary but do it anyway?
        FliSdk_V2.FliSerialCamera.EnableBias(context, False)
    res,state= FliSdk_V2.FliCred.GetBiasState(context)
    print("[DEBUGGING] State before correction: (should be false)")
    print(state)
    
    val = input("Cover lens and press any button...")
    print("Building bias")
    res = FliSdk_V2.FliCred.BuildBias(context)
    if not res:
        print("Error while building bias.")
        exit()
    print("Bias built! Enabling...")
    FliSdk_V2.FliSerialCamera.EnableBias(context, True)
    print("Bias Enabled!")
    print("[DEBUGGING]getting new bias state (should be true")
    res,state= FliSdk_V2.FliCred.GetBiasState(context)
    #print(res)
    print(state)
    input("Bias correction applied. Press enter to continue...")
def setConversionGain(context,conversionGain):
    """
    Sets the conversion gain for the given context.

    Parameters:
    context (object): The context in which to set the conversion gain.
    conversionGain (str): The desired conversion gain level. 
                            Accepted values are "low", "medium", and "high".

    Returns:
    None

    Prints a message indicating whether the conversion gain was successfully set.
    If an invalid conversion gain is provided, it defaults to "medium" and prints a warning message.
    """
    if conversionGain.lower()=="low":
        res =FliSdk_V2.FliCredThree.SetConversionGain(context, conversionGain.lower())
    elif conversionGain.lower()=="medium": 
        res=FliSdk_V2.FliCredThree.SetConversionGain(context, conversionGain.lower())
    elif conversionGain.lower()=="high":
        res=FliSdk_V2.FliCredThree.SetConversionGain(context, conversionGain.lower())
    else:
        print("Conversion gain not set. Default is Medium")
        conversionGain="medium"
        res=FliSdk_V2.FliCredThree.SetConversionGain(context, conversionGain.lower())
    if res:
        print("Conversion gain succesfully set to:",conversionGain)
def initCamera(context,frameRate,tintVal,conversionGain="Medium"):
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
    print("Detection of grabbers...")
    listOfGrabbers = FliSdk_V2.DetectGrabbers(context)

    if len(listOfGrabbers) == 0:
        print("No grabber detected, exit.")
        exit()

    print("Done.")
    print("List of detected grabber(s):")

    for s in listOfGrabbers:
        print("- " + s)

    print("Detection of cameras...")
    listOfCameras = FliSdk_V2.DetectCameras(context)

    if len(listOfCameras) == 0:
        print("No camera detected, exit.")
        exit()

    print("Done.")
    print("List of detected camera(s):")

    i = 0
    for s in listOfCameras:
        print("- " + str(i) + " -> " + s)
        i = i + 1

    cameraIndex = int(input("Which camera to use? (0, 1, ...) "))
    print("Setting camera: " + listOfCameras[cameraIndex])
    ok = FliSdk_V2.SetCamera(context, listOfCameras[cameraIndex])

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

    print("Done.")

    fps = 0

    if FliSdk_V2.IsSerialCamera(context):
        res, fps = FliSdk_V2.FliSerialCamera.GetFps(context)
    elif FliSdk_V2.IsCblueSfnc(context):
        res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)
    print("Previous camera FPS: " + str(fps))

    # val = input("FPS to set? ")
    val = frameRate
    setFPS(context,val)
    # try:
    #     valFloat = float(val)
    #     if FliSdk_V2.IsSerialCamera(context):
    #         FliSdk_V2.FliSerialCamera.SetFps(context, valFloat)
    #     elif FliSdk_V2.IsCblueSfnc(context):
    #         FliSdk_V2.FliCblueSfnc.SetAcquisitionFrameRate(context, valFloat)
    # except:
    #     print("Value is not a float")

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

    val = input("Conversion gain to set? (Low, Medium, High). Default is Medium")
    setConversionGain(context,val)
    
    #Setting buffer size (in acquisition now...?)
    #val = input("How many images to read? ")
    #val = float(bufferSize)
    # if not val.isnumeric():
    #     val = 600

context = FliSdk_V2.Init()
initCamera(context, 50, 1)
BuildNUCBias(context)
# context = FliSdk_V2.Init()
# FliSdk_V2.DetectGrabbers(context)
# cams = FliSdk_V2.DetectCameras(context)
# FliSdk_V2.SetCamera(context, cams[0])
# FliSdk_V2.SetMode(context, "Full")
# FliSdk_V2.Update(context)
# FliSdk_V2.FliSerialCamera.SetFps(context, 100)
# FliSdk_V2.FliCredThree.SetTint(context, 0.001)
# FliSdk_V2.Stop(context)
# FliSdk_V2.SetBufferSizeInImages(context, 4000)
# print(FliSdk_V2.GetBufferSize(context))
# print(FliSdk_V2.GetImagesCapacity(context))
# FliSdk_V2.Start(context)
# #plt.imshow(FliSdk_V2.GetRawImageAsNumpyArray(context, -1), cmap="gray")
# #plt.show()
# print(FliSdk_V2.FliCred.GetBiasState(context))
# FliSdk_V2.FliSerialCamera.EnableBias(context, True)
# print(FliSdk_V2.FliCred.GetBiasState(context))
# FliSdk_V2.FliSerialCamera.EnableBias(context, False)
# print(FliSdk_V2.FliCred.GetBiasState(context))
# #FliSdk_V2.FliCred.BuildBias(context)
# BuildNUCBias(context)

# FliSdk_V2.Exit(context)
    # camera.connect()
    # camera.configure(fps=300)
    # fs.FliCredThree.EnableAdaptbias(camera.context, False)
    # print(fs.FliCred.GetBiasState(camera.context))
    # print(fs.FliSerialCamera.EnableBias(camera.context, False))
    # print(fs.FliCred.GetBiasState(camera.context))
    # fs.Start(camera.context)
    # fs.EnableRingBuffer(camera.context, True)
    # fs.FliCred.BuildBias(camera.context)
    # fs.Exit(camera.context)
    #camera.build_bias()

    # exposures_N = 100
    # exposure_min = 1/1000
    # exposure_max = fs.FliCredThree.GetTintMax(camera.context)[1]
    # print(exposure_max)
    # exposures = np.linspace(exposure_min, exposure_max, exposures_N)
    # print("Exposures range: ", exposures)
    #
    # images_N = 10
    # for bias in ["Manual", "Off", "Adaptive"]:
    #     for conv_gain in ["Low", "Medium", "High"]:
    #         camera.configure(bias_type=bias, conversion_gain=conv_gain)
    #         if bias == "Manual":
    #             input("Enter to build bias")
    #             camera.build_bias()
    #             input("Enter to continue")
    #         for exposure in exposures:
    #             camera.configure(exposure=exposure)
    #             images = camera.get_images(images_N)
    #             _expo_act = camera.config["exposure"]
    #             tifffile.imwrite(f"Auto_expo_testing//{bias}_{conv_gain}_{_expo_act}.tiff", images, photometric="minisblack", imagej=True)





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
