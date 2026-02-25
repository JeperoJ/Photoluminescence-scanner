import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
from . import view
from . import model
import typing


def _var_callback(category, setting, tk_var):
    #self.view.(*args)
    print(category, setting, tk_var)
    pass


class ConfigController:
    def __init__(self, parent):
        self.parent = parent
        self.model = model.ConfigModel(self.parent)
        self.view = view.ConfigView(self.parent, self.model.cfg_dict)

        self.changed = {}
        for category in self.view.cfg_vars:
            for setting in self.view.cfg_vars[category]:
                self.view.cfg_vars[category][setting].trace_add("write", lambda: _var_callback(category, setting, self.view.cfg_vars[category][setting]))


if __name__ == "__main__":
    root = tk.Tk()
    controller = ConfigController(root)