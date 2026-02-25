import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
import typing

class ConfigView(ttk.Notebook):
    def __init__(self, parent, cfg_dict: dict[str, dict[str, dict[str, typing.Any]]], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        parent.attributes('-fullscreen', True)

        s = ttk.Style()
        s.configure('.', font=('Helvetica', 60))

        my_font = font.Font(family='Helvetica', size=32)
        parent.option_add("*Font", my_font)

        self.cfg_vars = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        for category in cfg_dict:
            cfg_frame = ConfigFrame(self, cfg_dict[category])
            self.cfg_vars[category] = cfg_frame.ctgr_vars
            cfg_frame.grid(row=0, column=0, sticky="nsew")
            self.add(cfg_frame, text=category)

class ConfigFrame(ttk.Frame):
    def __init__(self, parent, ctgr_dict: dict[str, dict[str, typing.Any]], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        weights = [1, 1, 10]
        padding = 5
        for i, weight in enumerate(weights):
            self.columnconfigure(i, weight=weight)

        self.ctgr_vars = {}

        for i, setting in enumerate(ctgr_dict):
            setting_dict = ctgr_dict[setting]
            ttk.Label(self, text=setting).grid(row=i, column=0, sticky="nsew", padx=padding, pady=padding)
            self.ctgr_vars[setting]= tk.StringVar(self)
            #self.rowconfigure(i, weight=1)

            if setting_dict["type"] == "dropdown":
                selector = ttk.Combobox(self, values=setting_dict["options"], state="readonly", textvariable=self.ctgr_vars[setting])
                selector.current(0)
                selector.grid(row=i, column=1, columnspan=2, sticky="nsew", padx=padding, pady=padding)

            if setting_dict["type"] == "range":
                ttk.Entry(self, textvariable=self.ctgr_vars[setting]).grid(row=i, column=1, sticky="new", padx=padding,
                                                                           pady=padding)
                self.scale = ttk.Scale(self, from_=setting_dict["min"], to=setting_dict["max"], orient="horizontal",
                                       command=lambda s: self.ctgr_vars[setting].set(f"{round(float(s))}"))
                self.scale.grid(row=i, column=2, sticky="nsew", padx=padding, pady=padding)

        test = ttk.Button(self, text="Test", command=lambda: [print(self.ctgr_vars[key].get()) for key in self.ctgr_vars])
        test.grid(row=2, column=0, sticky="nsew")


if __name__ == "__main__":
    camera_cfg = {
    "Gain" : {
        "type": "dropdown",
        "options": ["Low", "Medium", "High"],
    },
    "FPS": {
        "type": "range",
        "min": 1,
        "max": 600,
    }}
    cfg_dict = {"Camera": camera_cfg}
    #for i, key in enumerate(cfg_dict):
    #    print(i, key, cfg_dict[key])
    root = tk.Tk()
    ConfigView(root, cfg_dict).pack(fill="both", expand=True)
    root.mainloop()