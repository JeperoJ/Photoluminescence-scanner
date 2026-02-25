from . import camera
import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

import FliSdk_V2

class Cred3(camera.Camera):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.context = FliSdk_V2.Init()





    def list(self):
        pass