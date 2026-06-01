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
            config_dict = self._config_default | config_dict

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
        """
        directory = os.path.join(savePath, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.mkdir(directory)
        scan_name = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.raw"
        length = min(self.robot.config["length_upper"], self.robot.config["length_lower"]+self.config["offset"])
        #nImages = int(length / (self.robot.config["speed"] / 60) * frameRate)

        self.robot.handler.set_position(self.config["offset"], 0)  # Set offset (to see panel before the light bar)
        self.robot.handler.set_position(length, length - self.config["offset"])
        self.camera.start_recording()
        self.robot.handler.wait()
        self.camera.stop_recording()
        self.camera.save_recording(os.path.join(directory, scan_name))
        self.save_config(os.path.join(directory, "config.toml"))





#if __name__ == "__main__":
#
