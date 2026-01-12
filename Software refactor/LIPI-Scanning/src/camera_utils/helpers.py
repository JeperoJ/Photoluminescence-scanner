from .FLI_API import FliSdk_V2


def setFPS(context,val):
    try:
        valFloat = float(val)
        if FliSdk_V2.IsSerialCamera(context):
            FliSdk_V2.FliSerialCamera.SetFps(context, valFloat)
        elif FliSdk_V2.IsCblueSfnc(context):
            FliSdk_V2.FliCblueSfnc.SetAcquisitionFrameRate(context, valFloat)
    except:
        print("Value is not a float")

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