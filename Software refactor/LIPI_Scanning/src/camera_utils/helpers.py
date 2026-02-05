import FliSdk_V2
import logging

logger = logging.getLogger(__name__)


def set_fps(context,val):
    valFloat = float(val)
    if FliSdk_V2.IsSerialCamera(context):
        _, fps_old = FliSdk_V2.FliSerialCamera.GetFps(context)
        FliSdk_V2.FliSerialCamera.SetFps(context, valFloat)
        _, fps_new = FliSdk_V2.FliSerialCamera.GetFps(context)


    elif FliSdk_V2.IsCblueSfnc(context):
        _, fps_old = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)
        FliSdk_V2.FliCblueSfnc.SetAcquisitionFrameRate(context, valFloat)
        _, fps_new = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)

    logger.debug("Old camera FPS: " + str(fps_old))
    logger.info("Camera FPS successfully set to: " + str(fps_new))

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
    
    # Start the camera acquisition - bias building requires the camera to be running
    print("Starting camera acquisition for bias building...")
    FliSdk_V2.Start(context)
    
    print("Building bias")
    res = FliSdk_V2.FliCred.BuildBias(context)
    if not res:
        print(res)
        print("Error while building bias.")
        FliSdk_V2.Stop(context)
        raise ValueError("BIAS???")
    print("Bias built! Enabling...")
    FliSdk_V2.Stop(context)
    FliSdk_V2.FliSerialCamera.EnableBias(context, True)
    print("Bias Enabled!")
    print("[DEBUGGING]getting new bias state (should be true")
    res,state= FliSdk_V2.FliCred.GetBiasState(context)
    #print(res)
    print(state)

def EnableAdaptBias(context):
    """
    Enable Adaptive Bias for FLI C-RED 3.

    Parameters:
    context (object): The FLI SDK context.

    Returns:
    None
    """
    print("Adaptive bias correction for FLI C-RED 3 started.....") 
    #Check if bias is enables´d
    res,state= FliSdk_V2.FliCredThree.GetAdaptBiasState(context)
    if state:
        #Change bias to false to generate new bias. Not sure if necessary but do it anyway?
        FliSdk_V2.FliSerialCamera.EnableBias(context, False)
    FliSdk_V2.FliCredThree.EnableAdaptbias(context,True)
    print("Bias enabled!")

def PixelCorrect(context,state=True):
    """
    Correct bad pixels.

    Parameters:
    context (object): The FLI SDK context.
    state (bool): The state to set for bad pixel correction. Default is True.

    Returns:
    None
    """
    res,state_old=FliSdk_V2.FliCredThree.GetBadPixelState(context)
    FliSdk_V2.FliCredThree.EnableBadPixel(context,False) #Set default value to false
    if state:
        FliSdk_V2.FliCredThree.EnableBadPixel(context,True)