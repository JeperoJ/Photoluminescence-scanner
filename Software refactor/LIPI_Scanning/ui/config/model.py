from ...src import camera_utils

#Purpose: Wrap the camera functions

class ConfigModel:
    def __init__(self, parent):
        self.parent = parent
        camera_cfg = {
            "Gain": {
                "type": "dropdown",
                "options": ["Low", "Medium", "High"],
                "callback": camera_utils.set_camera_gain,
            },
            "FPS": {
                "type": "range",
                "min": 1,
                "max": 600,
            }}
        self.cfg_dict = {"Camera": camera_cfg}