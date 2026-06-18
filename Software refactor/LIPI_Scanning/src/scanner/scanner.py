import FliSdk_V2
from ..camera_utils import cred3
from ..gantry_utils import gantry
import tomlkit as tmlk
import os
import datetime

class Scanner:
    def __init__(self):
        #TODO: Figure out what actually makes sense to do with the gantry / robot
        self.configured = False

        self.camera = cred3.Cred3()
        self.robot = gantry.Gantry()

        self.config = {}
        self._config_default = {
            "offset" : 100,
            "focal_length" : 6,
            "lens_name" : "Bob",
            "filter_stack" : "Undefined",
            "modulation_freq" : 50
        }
        self.system_config = {
            "general" : self.config,
            "camera" : self.camera.config,
            "robot" : self.robot.config,
        }

    def __del__(self):
        self.camera.close()
        self.robot.close()

    def configure(self, config_dict=None, **settings):
        if config_dict is None:
            config_dict = settings

        if not self.configured:
            config_dict = self._config_default | config_dict #Python always select elements from second dictionary. This means that any keyword in both will always have the user value, and any only in default the default value

        for key, value in config_dict.items():
            print(key)
            self.config[key] = value

        self.configured = True

    def configure_system(self, config_dict=None):
        if config_dict is None:
            self.configure()
            self.camera.configure()
            self.robot.configure()
        else:
            self.configure(config_dict["general"])
            self.camera.configure(config_dict["camera"])
            self.robot.configure(config_dict["robot"])

    def save_config(self, filepath):
        with open(filepath, "w") as f:
            tmlk.dump(self.system_config, f)

    def load_config(self, filepath):
        with open(filepath, "r") as f:
            config_dict = tmlk.load(f)
            self.configure_system(config_dict)

    def auto_expose(self, iterations=10, move=True, position=1000):
        """
        Function to automatically adjust the exposure of the camera. Relies on the camera class having a built-in function for this.
        The attached robot and camera must be calibrated at initial settings. If not moving, robot does not need to be calibrated.
        Args:
            iterations:
            move (True): If the robot should be moved into the designated position to do the auto-exposure.
            position: Only relevant when parameter move=True. Sets the position at which the lower axis should move to, to do the auto-expose. Upper axis will be moved to position+offset
        """
        if move:
            #Error catching
            #if not self.robot.calibrated:
            #    raise ValueError("Robot is not calibrated. Please calibrate first.")
            #if position + self.config["offset"] > self.robot.config["length_upper"]:
            #    raise ValueError("Position would exceed length of upper axis")
            #if position > self.robot.config["length_lower"]:
            #    raise ValueError("Position would exceed length of lower axis")

            self.robot.handler.set_position(position+self.config["offset"], position)
            self.robot.handler.wait()
        self.camera.auto_expose(iterations=iterations)
        if move:
            self.robot.handler.set_position(0,0)
            self.robot.handler.wait()




    def scan(self, savePath):
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

        - On the variable length:
            The gantry initially starts with an offset on the upper axis (UA), then moves both the UA and the lower axis (LA) the same length.
            Because we use absolute positioning, it does this, by moving the UA to a position "x", and the LA to a position "x-offset".
            Therefore, the largest this value "x" can be, is the smallest of the length of the UA and the LA-offset.
        """
        directory = os.path.join(savePath, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.mkdir(directory)
        scan_name = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.raw"
        length = min(self.robot.config["length_upper"], self.robot.config["length_lower"]+self.config["offset"])

        buffer_size_images = int(2 * self.camera.config["fps"] * length / (self.robot.config["speed"] / 60))
        print(f"Buffer size images: {buffer_size_images}")
        FliSdk_V2.SetBufferSizeInImages(self.camera.context, buffer_size_images)
        print(f"Context buffer size: {FliSdk_V2.GetImagesCapacity(self.camera.context)}")
        #nImages = int(length / (self.robot.config["speed"] / 60) * frameRate)
        #In case not started, start camera buffer filling
        self.camera.start()
        #Set offset position and wait
        self.robot.handler.set_position(self.config["offset"], 0)  # Set offset (to see panel before the light bar)
        self.robot.handler.wait()
        #Store current buffer filling, for later saving
        self.camera.start_recording()
        #Set end position and wait for movement to be finished
        self.robot.handler.set_position(length, length - self.config["offset"])
        self.robot.handler.wait()
        #Stop camera, and get final buffer filling
        self.camera.stop_recording()
        #Save everything in between markers, as well as settings used
        self.camera.save_recording(os.path.join(directory, scan_name))
        self.save_config(os.path.join(directory, "config.toml"))





#if __name__ == "__main__":
#
