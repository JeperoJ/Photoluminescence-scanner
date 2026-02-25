import typing

class Config:
    """
    Defines the outline for the config. Collection of settings.
     - name (str): Name of the config
    """
    def __init__(self, name: str, ):
        self.name = name




    class Setting:
        """
        Defines a setting in the config schema
         - name (str): Name of the setting
         - values (Any): Initial value of the setting
         - state (bool): Is this setting relevant to the current config
         - dependent (bool): Should this setting be determined from other settings using calc
         - mutable (bool): Can this setting be changed or is it a hardware constant
        """
        def __init__(self,name: str, value, state: bool, dependent: bool, mutable: bool, callback=None,calc=None):
            self.name = name
            self.value = value
            self.state = state
            self.dependent = dependent
            self.mutable = mutable
            self.callback = callback
            self.calc = calc