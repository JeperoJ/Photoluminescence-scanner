import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
import copy
import typing
import os
import sys
import tomlkit

class ConfigInterface:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Config Interface")
        self.window.attributes('-fullscreen', True)
        self.window.withdraw()
        self.view = ttk.Frame(self.window)
        self.view.pack(fill="both", expand=True)
        self.settings = None
        self._settings_changed = {}
        self._cfg_frames = {}
        self._config_dir = os.path.abspath(os.path.expanduser("~//Documents//LIPI"))

        self.view.rowconfigure(0, weight=1)
        self.view.columnconfigure(0, weight=1)

        button_frame = ttk.Frame(self.view)
        button_frame.grid(row=1, column=0)

        for i in range(6):
            button_frame.columnconfigure(i, weight=1)

        #ttk.Button(button_frame, text="Test", command=lambda: print(f"{self.settings}\n{self.settings_changed}\n")).grid(row=0, column=0, sticky="nsew")
        self.apply_button = ttk.Button(button_frame, text="Apply", command=self._apply_button_func, state="disabled")
        self.apply_button.grid(row=0, column=1, sticky="nsew")
        self.undo_button = ttk.Button(button_frame, text="Undo", command=self._undo_button_func, state="disabled")
        self.undo_button.grid(row=0, column=2, sticky="nsew")
        self.save_button = ttk.Button(button_frame, text="Save", command=self._save_button_func, state="enabled")
        self.save_button.grid(row=0, column=3, sticky="nsew")
        ttk.Button(button_frame, text="Load", command=self._load_button_func).grid(row=0, column=4, sticky="nsew")
        ttk.Button(button_frame, text="Close", command=self._close_button_func).grid(row=0, column=5, sticky="nsew")

        nb = ttk.Notebook(self.view)
        nb.grid(row=0, column=0, sticky="nsew")
        nb.columnconfigure(0, weight=1)
        nb.rowconfigure(0, weight=1)

        #Camera Config
        camera_cfg = ConfigFrame(nb)
        camera_cfg.grid(row=0, column=0, sticky="nsew")
        camera_cfg.add(name="Gain", data_type=str,
                   values={"selector": "dropdown", "options": ["Low", "Medium", "High"], "default": "Medium"},
                       callback=self._callback)
        camera_cfg.add(name="FPS", data_type=int,
                   values={"selector": "range", "min": 1, "max": 600, "precision":0, "default": 300},
                       callback=self._callback)
        camera_cfg.add(name="Exposure", data_type=int,
                   values={"selector": "range", "min": 1, "max": 20, "precision":0, "default": 2},
                       callback=self._callback)
        #camera.add()
        nb.add(child=camera_cfg, text="Camera")
        self._settings_changed["Camera"] = camera_cfg.settings
        self._cfg_frames["Camera"] = camera_cfg

        #Gantry Config
        gantry_cfg = ConfigFrame(nb)
        gantry_cfg.grid(row=0, column=0, sticky="nsew")
        gantry_cfg.add(name="Length", data_type=int,
                       values={"selector": "range", "min": 1000, "max": 2100, "precision":0, "default": 2100},
                       callback=self._callback)
        gantry_cfg.add(name="Speed", data_type=int,
                       values={"selector": "range", "min": 1000, "max": 5000, "precision":0, "default": 5000},
                       callback=self._callback)

        nb.add(child=gantry_cfg, text="Gantry")
        self._settings_changed["Gantry"] = gantry_cfg.settings
        self._cfg_frames["Gantry"] = gantry_cfg

        #Lightbar Config
        lightbar_cfg = ConfigFrame(nb)
        lightbar_cfg.grid(row=0, column=0, sticky="nsew")
        lightbar_cfg.add(name="Light", data_type=bool,
                         values={"selector": "dropdown", "options":["True", "False"], "default": True},
                         callback=self._callback)
        lightbar_cfg.add(name="Current", data_type=float,
                         values={"selector": "range", "min": 0, "max": 3, "precision":2, "default": 1},
                         callback=self._callback)
        lightbar_cfg.add(name="Frequency", data_type=int,
                         values={"selector": "range", "min": 0, "max": 100, "precision":0, "default": 50},
                         callback=self._callback)

        nb.add(child=lightbar_cfg, text="Gantry")
        self._settings_changed["Lightbar"] = lightbar_cfg.settings
        self._cfg_frames["Lightbar"] = lightbar_cfg


        self._apply_button_func()

    def open(self, on_close):
        self.window.deiconify()
        on_close()

    def save(self, file_path):
        # Create the file (empty) or open for writing as requested
        try:
            with open(file_path, "w") as f:
                tomlkit.dump(self.settings, f)
        except Exception as e:
            print(f"Failed to create file '{file_path}': {e}")

    def load(self, file_path):
        try:
            with open(file_path, "r") as f:
                settings = tomlkit.loads(f.read())
        except Exception as e:
            print(f"Failed to load file '{file_path}': {e}")
        try:
            for key in settings.keys():
                self._cfg_frames[key].set(settings[key])
        except Exception as e:
            print(f"Failed to set config: {e}")

    def _apply_button_func(self):
        self.settings = copy.deepcopy(self._settings_changed)
        self.undo_button["state"] = "disabled"
        self.apply_button["state"] = "disabled"
        self.save_button["state"] = "enabled"

    def _undo_button_func(self):
        for key in self._cfg_frames.keys():
            self._cfg_frames[key].set(self.settings[key])
        self.undo_button["state"] = "disabled"
        self.apply_button["state"] = "disabled"
        self.save_button["state"] = "enabled"

    def _save_button_func(self):
        # Ensure the config directory exists and use it as the initial directory for the dialog.
        try:
            os.makedirs(self._config_dir, exist_ok=True)
        except Exception as e:
            print(f"Failed to create folder '{self._config_dir}': {e}")
            return None
        path = filedialog.asksaveasfilename(parent=self.window,
                                            initialdir=self._config_dir,
                                            defaultextension=".toml",
                                            filetypes=[("TOML files", "*.toml"), ("All files", "*")])
        if path == None:
            print("File save cancelled")

        self.save(path)

    def _load_button_func(self):
        try:
            path = filedialog.askopenfilename(parent=self.window,
                                              initialdir=self._config_dir,
                                              filetypes=[("TOML files", "*.toml"), ("All files", "*")])
        except Exception as e:
            print(f"Failed to open file '{path}': {e}")
            return None
        if path is None:
            print("File load cancelled")
        else:
            self.load(path)

    def _close_button_func(self):
        self._undo_button_func()
        self.window.withdraw()

    def _callback(self, *args):
        self.undo_button["state"] = "enabled"
        self.apply_button["state"] = "enabled"
        self.save_button["state"] = "disabled"


class ConfigFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.settings = {}
        self._variables = {}
        self.row = 0

        weights = [1, 1, 10]
        self.padding = 5
        for i, weight in enumerate(weights):
            self.columnconfigure(i, weight=weight)

    def add(self, name, data_type, values, callback=lambda *args: None):
        ttk.Label(self, text=name).grid(row=self.row, column=0, sticky="nsew", padx=self.padding, pady=self.padding)
        var = tk.StringVar(self, value=values["default"], name=name)
        var.trace("w", lambda *args: self._store_value(name, data_type, var))
        var.trace('w', callback)

        if values["selector"] == "dropdown":
            widget = ttk.Combobox(self, values=values["options"], state="readonly", textvariable=var)
            widget.grid(row=self.row, column=1, columnspan=2, sticky="nsew", padx=self.padding, pady=self.padding)

            def on_var_change(*args):
                widget.set(var.get())

        if values["selector"] == "range":
            def on_scale_change(s):
                var.set(round(float(s), values["precision"]))

            def on_var_change(*args):
                try:
                    value_set = float(var.get())
                    # if values["min"] <= val <= values["max"]:
                    #     scale.set(val)
                    if values["min"] > value_set:
                        var.set(values["min"])
                    elif values["max"] < value_set:
                        var.set(values["max"])
                    value_final = float(var.get())
                    scale.set(value_final)
                except ValueError:
                    pass

            entry = ttk.Entry(self, textvariable=var)
            entry.grid(row=self.row, column=1, sticky="new", padx=self.padding, pady=self.padding)
            
            scale = ttk.Scale(self, from_=values["min"], to=values["max"], orient="horizontal",
                            command=on_scale_change)
            scale.set(values["default"])
            scale.grid(row=self.row, column=2, sticky="nsew", padx=self.padding, pady=self.padding)
            
        # Trace variable changes to update scale when entry is edited
        var.trace('w', on_var_change)

        self.row += 1
        self._store_value(name, data_type, var)
        self._variables[name] = var

    def set(self, new_values: dict[str, typing.Any]):
        for setting in new_values:
            self._variables[setting].set(new_values[setting])

    def _store_value(self, name, data_type, var):
        try:
            self.settings[name] = data_type(var.get())
        except Exception as e:
            print(f"Setting value failed for {name}, with error: {e}")

if __name__ == "__main__":
    root = tk.Tk()

    root.attributes('-fullscreen', True)

    s = ttk.Style()
    s.configure('.', font=('Helvetica', 60))

    my_font = font.Font(family='Helvetica', size=32)
    root.option_add("*Font", my_font)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    config = ConfigInterface(root)
    ttk.Button(root, text="Open Config", command=config.open).pack(expand=True, fill="both")
    ttk.Button(root, text="Quit", command=root.destroy).pack(expand=True, fill="both")
    ttk.Button(root, text="Print", command=lambda: print(config.settings)).pack(expand=True, fill="both")


    print(f"config.settings\n")
    root.mainloop()