import sys
import os
from typing import Literal

fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

import FliSdk_V2
#import typing

class Cred3:
    """
    Wrapper for the CRED3 camera. Moves the required FliSdk context into an internally handled variable,
    and tries to make usage easier by putting all the handled special commands into easy functions.

    Camera settings:
        - FPS: 0 to 600
        - Exposure: 0 to 1/FPS
        - Bad pixel correction: True or False
        - Bias correction: Off, Manual, or Adaptive
            - For manual it is advised to build a bias frame with the function. Remember to do so with camera lens on.
        - Flat Correction: True or False
            -
        - Conversion gain: Low, Medium, or High
        -

    Class variables:
        - context: The FliSdk context if it is ever needed directly
        - width: Image pixel width
        - height: Image pixel height
        - connected: Has a camera been connected to the class instance
        - configured: Has the config command been run, setting all the desired and required settings.
        - calibrated: Has a dark frame been built with current settings. Must be true for ready check if bias correction is "Manual".

    Class methods:
        - is_ready(): Checks if current class state implies camera ready for operation. Does not check if class state reflects reality.

    """
    def __init__(self):
        self.context = FliSdk_V2.Init()
        self.width = 640
        self.height = 512
        self.connected = False
        self.configured = False
        self.calibrated = False

        self.config = {}
        self._config_default = {
            "fps": 300,
            "exposure": 1,
            "bad_pixel_correction": True,
            "bias_type": "Manual",
            "flat_correction": True,
            "conversion_gain": "Medium",
            "anti_blooming": True,
        }
        self._config_functions = {
            "fps": self._set_fps,
            "exposure": self._set_exposure,
            "bad_pixel_correction": self._toggle_bad_pixel_correction,
            "bias_type": self._set_bias_type,
            "flat_correction": self._toggle_flat,
            "conversion_gain": self._set_conversion_gain,
            "anti_blooming": self._toggle_anti_blooming
        }

        self._start_frame = None
        self._end_frame = None

    def close(self):
        self.stop()
        FliSdk_V2.Exit(self.context)

    def __del__(self):
        self.close()

    def list(self):
        if self.connected:
            self.disconnect()
        FliSdk_V2.DetectGrabbers(self.context)
        return FliSdk_V2.DetectCameras(self.context)

    def connect(self, camera=None):
        """
        Args:
            camera: Which camera to connect to, gotten from list function. If left as none, will attempt to auto connect

        Returns:
            None
        """

        if camera is None:
            print(self.list())
            camera = self.list()[0]

        response = FliSdk_V2.SetCamera(self.context, camera)
        if not response:
            raise ValueError(f"Camera could not be set. Got response {response}")

        res = FliSdk_V2.IsCredThree(self.context)
        print(res)
        #if not res:
        #    raise ValueError(f"Camera is wrong type. This implementation is made exclusively for the FLI CRED-3.")

        FliSdk_V2.SetMode(self.context, FliSdk_V2.Mode.Full)
        response = FliSdk_V2.Update(self.context)

        if not response:
            raise ValueError(f"Error while updating SDK. Got response {response}")

        print("Camera connected.")
        self.connected = True
        FliSdk_V2.ImageProcessing.EnableAutoClip(self.context, -1, False)
        print("Auto-clip disabled.")

    def disconnect(self):
        """
            Stops camera context using FLI API
        """
        self.stop()
        FliSdk_V2.Exit(self.context)
        self.connected = False
        self.calibrated = False
        self.context = FliSdk_V2.Init()

    def start(self):
        if not self.connected:
            raise ValueError("Class instance not connected to a camera. Run connect function first.")
        FliSdk_V2.Start(self.context)
        
    def stop(self):
        FliSdk_V2.Stop(self.context)

    def is_ready(self):
        ready = True
        ready = ready and self.connected
        ready = ready and self.configured
        if self.config["bias_type"] == "Manual":
            ready = ready and self.calibrated
        return ready

    def configure(self, config_dict=None, **settings):
        """

        Args:
            config_dict: Dictionary of what is desired to change, with settings

        Returns:

        """
        if not self.connected:
            raise ValueError("Class instance not connected to a camera. Run connect function first.")

        if config_dict is None:
            config_dict = settings

        if not self.configured:
            config_dict = self._config_default | config_dict

        for key, value in config_dict.items():
            print(key)
            if key not in self._config_default:
                raise ValueError(f"Invalid setting {key}. Valid settings are {self._config_default.keys()}")
            elif key == "fps":
                if "exposure" in config_dict:
                    continue
                else:
                    self._config_functions["fps"](config_dict["fps"])
                    self._config_functions["exposure"](self.config["exposure"])
                    continue
            elif key == "exposure":
                if "fps" in config_dict:
                    self._config_functions["fps"](config_dict["fps"])
                    self._config_functions["exposure"](config_dict["exposure"])
                    continue
            self._config_functions[key](value)

        self.configured = True

    def start_recording(self):
        if not self.is_ready():
            raise ValueError("Camera is not ready. Please do setup before recording.")
        self._start_frame = FliSdk_V2.GetBufferFilling(self.context)

    def stop_recording(self):
        if self._start_frame is None:
            raise ValueError("Recording was never started.")
        self._end_frame = FliSdk_V2.GetBufferFilling(self.context)


    def save_recording(self, filepath):
        if self._start_frame is None:
            raise ValueError("Recording was never started.")

        if self._end_frame is None:
            self.stop_recording()

        FliSdk_V2.SaveBuffer(self.context, filepath, self._start_frame, self._end_frame)

    
    def build_bias(self):
        print("Building bias image")
        res = FliSdk_V2.FliCred.BuildBias(self.context)
        if not res:
            raise ValueError("Error while building bias.")
        print("Bias built successfully")
        self.calibrated = True

    def build_flat(self):
        print("Building flat image")
        res = FliSdk_V2.FliCred.BuildFlat(self.context)
        if not res:
            raise ValueError("Error while building flat.")
        print("Flat built successfully")

    # def _BuildNUCBias_legacy(self, frames=256):
    #     """
    #     Build NUC Bias for FLI C-RED 3.
    #
    #     Parameters:
    #     context (object): The FLI SDK context.
    #
    #     Returns:
    #     None
    #     """
    #     print("NUC Bias correction for FLI C-RED 3 started.....")
    #     print("[DEBUGGING]getting current bias state")
    #     # _, state = FliSdk_V2.FliCred.GetBiasState(self.context)
    #     # if state:
    #     #     # Change bias to false to generate new bias. Not sure if necessary but do it anyway?
    #     #     FliSdk_V2.FliSerialCamera.EnableBias(context, False)
    #     state_before, _ = self._toggle_bias(False)
    #     #res, state = FliSdk_V2.FliCred.GetBiasState(context)
    #     print("[DEBUGGING] State before correction: (should be false)")
    #     print(state_before)
    #
    #     # Start the camera acquisition - bias building requires the camera to be running
    #     print("Starting camera acquisition for bias building...")
    #     FliSdk_V2.Start(self.context)
    #
    #     print("Building bias")
    #     res = FliSdk_V2.FliCred.BuildBias(self.context)
    #     if not res:
    #         print(res)
    #         print("Error while building bias.")
    #         self.stop()
    #         raise ValueError("BIAS???")
    #     print("Bias built! Enabling...")
    #     self.stop()
    #     FliSdk_V2.FliSerialCamera.EnableBias(self.context, True)
    #     print("Bias Enabled!")
    #     print("[DEBUGGING]getting new bias state (should be true")
    #     res, state = FliSdk_V2.FliCred.GetBiasState(self.context)
    #     # print(res)
    #     print(state)
    #     self.calibrated = True

    def _set_bias_type(self, bias_type: Literal["Off", "Manual", "Adaptive"]):
        print("Setting bias for FLI C-RED 3.")
        state_bias = False
        state_adaptive = False
        if bias_type == "Manual":
            state_bias = True
        if bias_type == "Adaptive":
            state_adaptive = True
        self._toggle_bias(state_bias)
        self._toggle_bias(state_adaptive)
        self.config["bias_type"] = bias_type

    def _set_conversion_gain(self, conversion_gain: Literal["low", "medium", "high"]):
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
        gain = conversion_gain.lower()
        if gain in ["low","medium","high"]:
            res = FliSdk_V2.FliCredThree.SetConversionGain(self.context, gain)
            if res:
                print("Conversion gain succesfully set to:", conversion_gain)
            else:
                raise ValueError(f"Conversion gain could not be set. Got response {res}")
            self.config["conversion_gain"] = conversion_gain
        else:
            raise ValueError(f"Conversion gain '{conversion_gain}' is not supported.")

    def _set_value(self, setting, cfg_key, setter, getter):
        self.calibrated = False
        _, value_old = getter()
        res = setter()
        if not res:
            raise ValueError(f"Error setting {setting}.")
        _, value_new = getter()
        print(f"Old {setting}: {value_old}, New {setting}: {value_new}")
        if cfg_key is not None:
            self.config[cfg_key] = value_new

    def _set_fps(self, fps: float):
        self._set_value(
            setting = "FPS",
            cfg_key = "fps",
            setter = lambda: FliSdk_V2.FliSerialCamera.SetFps(self.context, fps),
            getter = lambda: FliSdk_V2.FliSerialCamera.GetFps(self.context)
        )

    def _set_exposure(self, exposure: float):
        if exposure > 1000/self.config["fps"]:
            raise ValueError("Exposure too high")

        self._set_value(
            setting = "Exposure",
            cfg_key = "exposure",
            getter = lambda: FliSdk_V2.FliCredThree.GetTint(self.context),
            setter = lambda: FliSdk_V2.FliCredThree.SetTint(self.context, exposure)
        )

    def _toggle(self, setting, setter, getter, cfg_key=None):
        self.calibrated = False
        _, state_old = getter()
        res = setter()
        if not res:
            print(state_old)
            print(res)
            raise ValueError(f"{setting} state could not be set. Got response {res}")
        _, state_new = getter()
        print(f"{setting} state changed from {state_old} to {state_new}")
        if cfg_key is not None:
            self.config[cfg_key] = state_new

    def _toggle_bias(self, state: bool):
        return self._toggle("Bias Correction",
                     setter=lambda: FliSdk_V2.FliSerialCamera.EnableBias(self.context, state),
                     getter=lambda: FliSdk_V2.FliCred.GetBiasState(self.context)
                     )

    def _toggle_adaptive_bias(self, state: bool):
        """
        Enable Adaptive Bias for FLI C-RED 3.

        Parameters:
        context (object): The FLI SDK context.

        Returns:
        None
        """
        return self._toggle("Adaptive Bias",
                     setter=lambda: FliSdk_V2.FliCredThree.EnableAdaptbias(self.context, state),
                     getter=lambda: FliSdk_V2.FliCredThree.GetAdaptBiasState(self.context)
                     )

    def _toggle_flat(self, state: bool):
        pass
        # return self._toggle("Flat Correction",
        #              cfg_key = "flat_correction",
        #              setter=lambda: FliSdk_V2.FliSerialCamera.EnableFlat(self.context, state),
        #              getter=lambda: FliSdk_V2.FliCred.GetFlatState(self.context)
        #              )

    def _toggle_anti_blooming(self, state: bool):
        return self._toggle("Anti Blooming",
                            cfg_key = "anti_blooming",
                            setter=lambda: FliSdk_V2.FliCredThree.EnableAntiBlooming(self.context, state),
                            getter=lambda: FliSdk_V2.FliCredThree.GetAntiBloomingState(self.context))

    def _toggle_bad_pixel_correction(self, state: bool):
        """
            Correct bad pixels.

            Parameters:
            context (object): The FLI SDK context.
            state (bool): The state to set for bad pixel correction.

            Returns:
            None
            """
        return self._toggle("Bad Pixel correction",
                            cfg_key="bad_pixel_correction",
                            setter=lambda: FliSdk_V2.FliCredThree.EnableBadPixel(self.context, state),
                            getter=lambda: FliSdk_V2.FliCredThree.GetBadPixelState(self.context)
                            )




#Cut outs
# self.config_schema = {
        #     "fps": {"type": float, "values": {"min":1, "max":601}, "default": 300},
        #     "exposure": {"type": float, "values": {"min":0, "max":1000}, "default":2},
        #     "adaptive_bias": {"type": bool, "default": False},
        #     "gain": {"type": str, "values": ["Low", "Medium", "High"], "default": "Medium"},
        #     "hdr": {"type": bool, "default": False},
        #     "anti_blooming": {"type": bool, "default": True},
        #     "bad_pixel_correction": {"type": bool, "default": True},
        # }