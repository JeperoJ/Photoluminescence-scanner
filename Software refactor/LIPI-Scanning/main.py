"""
UI:

Basic Elements:
Select Gantry Port and Calibrate
Select Camera and adjust default settings
Select where to save images


Advanced parts:
Preview while scanning / Camera Stream
More settings available
Exposure Adjustment (Requires starting and stopping the context i think. Wonder how fast this is?)
"""


import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
from src import gantry_utils
root = tk.Tk()
root.attributes('-fullscreen', True)
#root.overrideredirect(True)
#width = root.winfo_screenwidth()
#height = root.winfo_screenheight()
#frm = ttk.Frame(root)
#frm.pack(fill=tk.BOTH, expand=True)
#frm.grid()
tk.Grid.rowconfigure(root, 0, weight=1)
tk.Grid.rowconfigure(root, 1, weight=1)
tk.Grid.rowconfigure(root, 2, weight=1)
tk.Grid.columnconfigure(root, 0, weight=1)
tk.Grid.columnconfigure(root, 1, weight=1)

s = ttk.Style()
s.configure('.', font=('Helvetica', 60))

my_font = font.Font(family='Helvetica', size=32)
root.option_add("*Font", my_font)

def calibrate_gantry(): #TODO: Figure out import from PLRobot / Submodule, or write simple function / wrapper
    print("Not done!")

def calibrate_camera(): #TODO: Figure out import from Submodule, or write simple function / wrapper
    print("Not done!")

def scan_module(): #TODO: Implement this using the variables present in the UI
    print("Not done!")

def update():
    print("UPDATING")

def select_directory():
    dir_path = filedialog.askdirectory()
    print(f"Selected directory: {dir_path}")
    save_dir_text.set(dir_path)

def grid_make(widget, row, column, padding=5):
    widget_return = widget
    widget_return.grid(row=row, column=column, sticky="nsew", padx=padding, pady=padding)
    return widget_return

#my_font = font.Font(family='Helvetica', size=46)

#Gantry
print(gantry_utils.get_ports())
gantry_dropdown = grid_make(ttk.Combobox(root, values=gantry_utils.get_ports()), 0, 0)
grid_make(ttk.Button(root, text="Calibrate Gantry", command=calibrate_gantry), 0, 1)

#Camera
camera_dropdown = grid_make(ttk.Combobox(root, values=["Option 1", "Option 2"]), 1, 0)
grid_make(ttk.Button(root, text="Calibrate Camera", command=calibrate_camera), 1, 1)

#Directory
save_dir_frm = grid_make(ttk.Frame(root), 2, 0)
tk.Grid.columnconfigure(save_dir_frm, 0, weight=1)
tk.Grid.rowconfigure(save_dir_frm, 0, weight=2)
tk.Grid.rowconfigure(save_dir_frm, 1, weight=8)
save_dir_text = tk.StringVar()
grid_make(ttk.Entry(save_dir_frm, textvariable=save_dir_text, font=("Helvetica", 18)), 0, 0, padding=0)
grid_make(ttk.Button(save_dir_frm, text="Select Directory", command=select_directory), 1, 0, padding=0)

#Start Scan
grid_make(ttk.Button(root, text="Start Scan", command=scan_module), 2, 1)

root.mainloop()


"""
UI Pseudo Structure
Home screen:
    Collumn
        Row
            Dropdown - COM Ports
            Settings
        Row
            Dropdown - Camera Ports
            Settings
        Row
            Text Box - Filename
            Button - Choose Directory
            Button - Start scan


"""