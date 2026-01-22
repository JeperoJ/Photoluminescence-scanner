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


from multiprocessing import context
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
import sys
import os
import tomlkit
import numpy as np
from  PIL import ImageTk, Image
from src import gantry_utils
from src import camera_utils
from src.camera_utils.FLI_API import FliSdk_V2

class LIPI_Scanner_App():
    def __init__(self, parent):
            #Initializing Application Variables
            self.parent = parent
            with open("LIPI-Scanning/data/config/default.toml", "r") as f:
                self.config = tomlkit.load(f)
            self.fps = self.config["camera"]["fps"]
            self.tint = self.config["camera"]["tint"]
            self.gain = self.config["camera"]["gain"]
            self.speed = self.config["gantry"]["speed"]
    
            self.camera_context = FliSdk_V2.Init()
            self.gantry_handler = None

            #UI Elements

            #Gantry
            com_ports = gantry_utils.get_ports()
            self.gantry_dropdown = ttk.Combobox(self.parent, values=com_ports, state="readonly", postcommand=self.update)
            self.gantry_button = ttk.Button(self.parent, text="Connect Gantry", command=self.connect_gantry)
            #Camera
            self.camera_dropdown = ttk.Combobox(self.parent, values=camera_utils.list(self.camera_context), state="readonly", postcommand=lambda: self.camera_dropdown.config(values=camera_utils.list(self.camera_context)))
            self.camera_button = ttk.Button(self.parent, text="Connect Camera", command=self.connect_camera)
            self.camera_preview_button = ttk.Button(self.parent, text="Preview", command=self.show_camera, state="disabled")

            self.save_dir_frm = ttk.Frame(self.parent)
            tk.Grid.columnconfigure(self.save_dir_frm, 0, weight=1)
            tk.Grid.rowconfigure(self.save_dir_frm, 0, weight=2)
            tk.Grid.rowconfigure(self.save_dir_frm, 1, weight=8)
            save_dir_text = tk.StringVar()
            ttk.Entry(self.save_dir_frm, textvariable=save_dir_text, font=("Helvetica", 18)).grid(row=0, column=0)
            ttk.Button(self.save_dir_frm, text="Select Directory", command=self.select_directory).grid(row=1, column=0)


            self.scan_module_button = ttk.Button(self.parent, text="Start Scan", state="disabled", command=self.scan_module)

            self.quit_button = ttk.Button(self.parent, text="Quit", command=quit)

            #UI Appearance

            self.parent.attributes('-fullscreen', True)
            self.parent.protocol("WM_DELETE_WINDOW", quit)
            #Style Settings
            tk.Grid.rowconfigure(self.parent, 0, weight=1)
            tk.Grid.rowconfigure(self.parent, 1, weight=1)
            tk.Grid.rowconfigure(self.parent, 2, weight=1)
            tk.Grid.columnconfigure(self.parent, 0, weight=10)
            tk.Grid.columnconfigure(self.parent, 1, weight=10)
            tk.Grid.columnconfigure(self.parent, 2, weight=1)

            s = ttk.Style()
            s.configure('.', font=('Helvetica', 60))

            my_font = font.Font(family='Helvetica', size=32)
            self.parent.option_add("*Font", my_font)

            #Organizing UI Elements
            padding = 5
            self.gantry_dropdown.grid(row=0, column=0, sticky="nsew", padx=padding, pady=padding)
            self.gantry_button.grid(row=0, column=1, sticky="nsew", padx=padding, pady=padding)

            self.camera_dropdown.grid(row=1, column=0, sticky="nsew", padx=padding, pady=padding)
            self.camera_button.grid(row=1, column=1, sticky="nsew", padx=padding, pady=padding)
            self.camera_preview_button.grid(row=1, column=2, sticky="nsew", padx=padding, pady=padding)

            self.save_dir_frm.grid(row=2, column=0, sticky="nsew", padx=padding, pady=padding)
            self.scan_module_button.grid(row=2, column=1, sticky="nsew", padx=padding, pady=padding)
            self.quit_button.grid(row=2, column=2, sticky="nsew", padx=padding, pady=padding)


    def update(self):
    #print("UPDATING")
        self.com_ports = gantry_utils.get_ports()
        self.gantry_dropdown.config(values=self.com_ports)
        if str(self.camera_button["state"]) == "disabled" and str(self.gantry_button["state"]) == "disabled" and save_dir_text.get() != "":
            self.scan_module_button.config(state="enabled")

    def quit(self):
        camera_utils.disconnect(self.camera_context)
        if self.gantry_handler is not None:
            self.gantry_handler.disconnect()
        self.parent.destroy()
        sys.exit()

    def popup(self, title, text, dismiss=False):
        popup = tk.Toplevel(self.parent)
        popup.title(title)
        #popup.geometry("600x200")
        popup.grab_set()  # Make modal, locks root window
        ttk.Label(popup, text=text).pack(pady=10)
        popup.update()
        if dismiss:
            ttk.Button(popup, text="OK", command=popup.destroy).pack()
            self.parent.wait_window(popup)  # Wait for popup to close
        if not dismiss:
            return popup

    #Gantry
    def connect_gantry(self):
        _popup = self.popup("Gantry Connection", "Connecting to gantry. Please wait...")
        self.gantry_handler = gantry_utils.connect(self.com_ports[[str(port) for port in self.com_ports].index(self.gantry_dropdown.get())])
        self.gantry_button.config(text="Calibrate Gantry", command=self.calibrate_gantry)
        _popup.destroy()
        self.update()

    def calibrate_gantry(self):
        self.popup("Gantry Calibration", "Please make sure the gantry area is clear and press OK to continue.", dismiss=True)
        _popup = self.popup("Gantry Calibration", "Calibrating gantry. Please wait...")
        gantry_utils.calibrate(self.gantry_handler)
        self.gantry_button.config(text="Gantry Ready", state="disabled")
        _popup.destroy()
        self.update()

    #Camera
    def connect_camera(self):
        global camera_state
        _popup = self.popup("Camera Initialization", "Connecting to camera. Please wait...")
        _popup.update()
        camera_utils.init_camera(self.camera_context, self.fps, self.tint, self.camera_dropdown.get(), gain=self.gain)
        self.camera_button.config(text="Calibrate", command=self.calibrate_camera)
        _popup.destroy()
        self.update()

    def calibrate_camera(self):
        self.popup("Camera Calibration", "Please put on the camera lens cap and press OK to continue.", dismiss=True)
        _popup = self.popup("Camera Calibration", "Calibrating camera. Please wait...")
        _popup.update()
        camera_utils.calibrate_camera(self.camera_context, adaptiveBias=False)
        self.camera_button.config(text="Camera Ready", state="disabled")
        _popup.destroy()
        self.camera_preview_button.config(state="enabled")
        self.update()

    def show_image_loop(self, window, image_label):
        image = FliSdk_V2.GetProcessedImageRGBANumpyArray(self.camera_context, -1) #-1 to get the last image in the buffer
        #print(image)
        #print(np.array(image))
        img = Image.fromarray(image, mode="RGBA")
        photo = ImageTk.PhotoImage(image=img)
        image_label.image = photo
        image_label.configure(image=photo)
        window.update()
        window.after(20, self.show_image_loop, window, image_label)

    def show_camera(self):
        popup = tk.Toplevel(self.parent)
        popup.title("Camera Preview")
        #popup.geometry("600x200")
        popup.grab_set()  # Make modal, locks root window
        FliSdk_V2.ImageProcessing.EnableAutoClip(self.camera_context, -1, True)
        FliSdk_V2.ImageProcessing.SetColorMap(self.camera_context, -1, "RAINBOW")
        FliSdk_V2.Start(self.camera_context)
        image_label = tk.Label(popup)
        image_label.pack(pady=10, fill="both", expand=True)
        ttk.Button(popup, text="Close", command=popup.destroy).pack()
        self.show_image_loop(popup, image_label)
        self.parent.wait_window(popup)  # Wait for popup to close
        FliSdk_V2.Stop(self.camera_context)

    def select_directory(self):
        dir_path = filedialog.askdirectory()
        #print(f"Selected directory: {dir_path}")
        self.save_dir_text.set(dir_path)
        self.update()

    def scan_module(self): #TODO: Implement this using the variables present in the UI
        self.scan_module_button.config(text="Interupt", command=quit)
        gantry_utils.scan_continuous(self.gantry_handler,self.camera_context,self.save_dir_text.get(),self.fps,self.speed)
        print("Not done!")
        

def main():
    root = tk.Tk()
    LIPI_Scanner_App(root)
    root.mainloop()

if __name__ == "__main__":
    main()