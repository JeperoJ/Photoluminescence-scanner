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
import sys
import os
from src import gantry_utils
from src import camera_utils

root = tk.Tk()
#root.attributes('-fullscreen', True)
tk.Grid.rowconfigure(root, 0, weight=1)
tk.Grid.rowconfigure(root, 1, weight=1)
tk.Grid.rowconfigure(root, 2, weight=1)
tk.Grid.columnconfigure(root, 0, weight=1)
tk.Grid.columnconfigure(root, 1, weight=1)

s = ttk.Style()
s.configure('.', font=('Helvetica', 60))

my_font = font.Font(family='Helvetica', size=32)
root.option_add("*Font", my_font)
global camera_context
global gantry_handler
global gantry_state
global camera_state
global fps
global gain
global tint

gantry_state = None
camera_state = None
camera_context = camera_utils.start_context()
fps = 50
gain = "Medium"
tint = 1 #Exposure time in ms
speed = 5000

def update():
    print("UPDATING")
    if gantry_state == "Calibrated" and camera_state == "Calibrated" and save_dir_text.get() != "":
        scan_module_button.config(state="enabled")

def quit():
    root.destroy()
    sys.exit()
    if camera_state is not None:
        camera_utils.disconnect(camera_context)
    if gantry_state is not None:
        gantry_handler.disconnect()

def grid_make(widget, row, column, padding=5):
    widget_return = widget
    widget_return.grid(row=row, column=column, sticky="nsew", padx=padding, pady=padding)
    return widget_return

def interrupt_popup(title,text):
    popup = tk.Toplevel(root)
    popup.title(title)
    #popup.geometry("600x200")
    popup.grab_set()  # Make modal, locks root window
    ttk.Label(popup, text=text).pack(pady=10)
    ttk.Button(popup, text="OK", command=popup.destroy).pack()
    root.wait_window(popup)  # Wait for popup to close

#Gantry
def connect_gantry():
    global gantry_state
    global gantry_handler
    print(gantry_dropdown.get())
    gantry_handler = gantry_utils.connect(com_ports[[str(port) for port in com_ports].index(gantry_dropdown.get())])
    gantry_button.config(text="Calibrate Gantry", command=calibrate_gantry)
    gantry_state = "Connected"
    update()

def calibrate_gantry():
    interrupt_popup("Gantry Calibration", "Please make sure the gantry area is clear and press OK to continue.")
    gantry_utils.calibrate(gantry_handler)
    gantry_button.config(text="Gantry Calibrated", state="disabled")
    global gantry_state
    gantry_state = "Calibrated"
    update()

com_ports = gantry_utils.get_ports()
gantry_dropdown = grid_make(ttk.Combobox(root, values=com_ports, state="readonly"), 0, 0)
gantry_button = grid_make(ttk.Button(root, text="Connect Gantry", command=connect_gantry), 0, 1)

#Camera
def init_camera():
    camera_utils.init_camera(camera_context, fps, tint, camera_dropdown.get(), gain=gain)
    camera_button.config(text="Calibrate", command=calibrate_camera)
    update()

def calibrate_camera(): #TODO: Figure out import from Submodule, or write simple function / wrapper
    global camera_calibrated
    interrupt_popup("Camera Calibration", "Please place the camera lens cap and press OK to continue.")
    camera_utils.calibrate_camera(camera_context, adaptiveBias=False)
    camera_calibrated = True
    update()

camera_list = camera_utils.list(camera_context)
camera_dropdown = grid_make(ttk.Combobox(root, values=camera_list, state="readonly"), 1, 0)
camera_button = grid_make(ttk.Button(root, text="Calibrate Camera", command=init_camera), 1, 1)

#Directory
def select_directory():
    dir_path = filedialog.askdirectory()
    print(f"Selected directory: {dir_path}")
    save_dir_text.set(dir_path)
    update()

save_dir_frm = grid_make(ttk.Frame(root), 2, 0)
tk.Grid.columnconfigure(save_dir_frm, 0, weight=1)
tk.Grid.rowconfigure(save_dir_frm, 0, weight=2)
tk.Grid.rowconfigure(save_dir_frm, 1, weight=8)
save_dir_text = tk.StringVar()
grid_make(ttk.Entry(save_dir_frm, textvariable=save_dir_text, font=("Helvetica", 18)), 0, 0, padding=0)
grid_make(ttk.Button(save_dir_frm, text="Select Directory", command=select_directory), 1, 0, padding=0)

#Start Scan
def scan_module(): #TODO: Implement this using the variables present in the UI
    scan_module_button.config(text="Interupt", command=quit)
    gantry_utils.scan_continuous(gantry_handler,camera_context,save_dir_text.get(),fps,speed)
    print("Not done!")

scan_module_button = grid_make(ttk.Button(root, text="Start Scan", state="disabled", command=scan_module), 2, 1)

root.protocol("WM_DELETE_WINDOW", quit)

root.mainloop()