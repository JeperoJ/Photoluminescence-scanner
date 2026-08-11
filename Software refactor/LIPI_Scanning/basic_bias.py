import os
import sys
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)
import FliSdk_V2

context = FliSdk_V2.Init()
FliSdk_V2.DetectGrabbers(context)
cams = FliSdk_V2.DetectCameras(context)
res = FliSdk_V2.SetCamera(context, cams[0])
if not res:
    print("Could not connect to camera")
    exit()
FliSdk_V2.SetMode(context, "Full")
FliSdk_V2.Update(context)
FliSdk_V2.Start(context)
FliSdk_V2.FliSerialCamera.EnableBias(context, False)
FliSdk_V2.FliCred.BuildBias(context)
print("Successfully build bias")