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
import threading
import time
import datetime

class LIPI_Scanner_App(ttk.Frame):
    def __init__(self, parent):
            #Initializing Application Variables
            ttk.Frame.__init__(self, parent)
            self = self
            #with open("LIPI-Scanning/data/config/default.toml", "r") as f:
            #    self.config = tomlkit.load(f)
            self.fps = 300
            self.tint = 0.5
            self.gain = "Medium"
            self.gantry_speed = 5000 #mm/min
            #self.fps = self.config["camera"]["fps"]
            #self.tint = self.config["camera"]["tint"]
            #self.gain = self.config["camera"]["gain"]
            #self.gantry_speed = self.config["gantry"]["speed"] #mm/min
            self.gantry_length = 2100 #mm #TODO: Add to config (Make proper gantry config)

    
            self.camera_context = FliSdk_V2.Init()
            self.gantry_handler = None

            #print(FliSdk_V2.ImageProcessing.GetColorMapList(self.camera_context, -1))

            #UI Appearance

            parent.attributes('-fullscreen', True)
            parent.protocol("WM_DELETE_WINDOW", quit)
            s = ttk.Style()
            s.configure('.', font=('Helvetica', 60))

            my_font = font.Font(family='Helvetica', size=32)
            parent.option_add("*Font", my_font)

            #UI Elements

            #Gantry
            com_ports = gantry_utils.get_ports()
            self.gantry_dropdown = ttk.Combobox(self, values=com_ports, state="readonly", postcommand=self.update)
            self.gantry_button = ttk.Button(self, text="Connect\nGantry", command=self.connect_gantry)
            #Camera
            self.camera_dropdown = ttk.Combobox(self, values=camera_utils.list(self.camera_context), state="readonly", postcommand=lambda: self.camera_dropdown.config(values=camera_utils.list(self.camera_context)))
            self.camera_button = ttk.Button(self, text="Connect\nCamera", command=self.connect_camera)
            #self.camera_preview_button = ttk.Button(self, text="Preview", command=self.show_camera, state="disabled")

            self.save_dir_frm = ttk.Frame(self)
            tk.Grid.columnconfigure(self.save_dir_frm, 0, weight=1)
            tk.Grid.rowconfigure(self.save_dir_frm, 0, weight=2)
            tk.Grid.rowconfigure(self.save_dir_frm, 1, weight=8)
            self.save_dir_text = tk.StringVar()
            ttk.Entry(self.save_dir_frm, textvariable=self.save_dir_text, font=("Helvetica", 18)).grid(row=0, column=0, sticky="nsew")
            ttk.Button(self.save_dir_frm, text="Select\nDirectory", command=self.select_directory).grid(row=1, column=0, sticky="nsew")

            self.button_config = ttk.Button(self, text="Config\n(TBD)", state="disabled") #TODO: Implement Config Window

            self.preview_frm = ttk.Frame(self, width=640, height=512)
            self.preview = ttk.Label(self.preview_frm)
            self.preview.pack(fill="both", expand=True)
            #self.preview.pack(fill="both", expand=True)


            self.scan_module_button = ttk.Button(self, text="Start\nScan", state="disabled", command=self.scan_module)

            self.quit_button = ttk.Button(self, text="Quit", command=quit)

            #Organizing UI Elements
            row_weights = [1,1,1]
            col_weights = [1,1,1,1]
            for i, weight in enumerate(row_weights):
                tk.Grid.rowconfigure(self, i, weight=weight)
            for i, weight in enumerate(col_weights):
                tk.Grid.columnconfigure(self, i, weight=weight)
            """ tk.Grid.rowconfigure(self, 0, weight=1)
            tk.Grid.rowconfigure(self, 1, weight=1)
            tk.Grid.rowconfigure(self, 2, weight=1)
            tk.Grid.columnconfigure(self, 0, weight=1)
            tk.Grid.columnconfigure(self, 1, weight=1)
            tk.Grid.columnconfigure(self, 2, weight=1)
            tk.Grid.columnconfigure(self, 3, weight=1) """

            padding = 5
            self.gantry_dropdown.grid(row=0, column=0, sticky="nsew", padx=padding, pady=padding)
            self.gantry_button.grid(row=0, column=1, sticky="nsew", padx=padding, pady=padding)

            self.camera_dropdown.grid(row=1, column=0, sticky="nsew", padx=padding, pady=padding)
            self.camera_button.grid(row=1, column=1, sticky="nsew", padx=padding, pady=padding)
            #self.camera_preview_button.grid(row=1, column=2, sticky="nsew", padx=padding, pady=padding)

            self.button_config.grid(row=2, column=1, sticky="nsew", padx=padding, pady=padding)
            self.save_dir_frm.grid(row=2, column=0, sticky="nsew", padx=padding, pady=padding)


            self.preview_frm.grid(row=0, column=2, rowspan=2, columnspan=2, sticky="nsew", padx=padding, pady=padding)
            self.scan_module_button.grid(row=2, column=2, sticky="nsew", padx=padding, pady=padding)
            self.quit_button.grid(row=2, column=3, sticky="nsew", padx=padding, pady=padding)
            


    def update(self):
    #print("UPDATING")
        self.com_ports = gantry_utils.get_ports()
        self.gantry_dropdown.config(values=self.com_ports)
        if str(self.camera_button["state"]) == "disabled" and str(self.gantry_button["state"]) == "disabled" and self.save_dir_text.get() != "":
            self.scan_module_button.config(state="enabled")

    def quit(self):
        camera_utils.disconnect(self.camera_context)
        if self.gantry_handler is not None:
            self.gantry_handler.disconnect()
        self.destroy()
        sys.exit()

    def popup(self, title, text, dismiss=False):
        popup = tk.Toplevel(self)
        popup.title(title)
        #popup.geometry("600x200")
        popup.grab_set()  # Make modal, locks root window
        ttk.Label(popup, text=text).pack(pady=10)
        popup.update()
        if dismiss:
            ttk.Button(popup, text="OK", command=popup.destroy).pack()
            self.wait_window(popup)  # Wait for popup to close
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
        #FliSdk_V2.ImageProcessing.EnableAutoClip(self.camera_context, -1, True) #TODO: Clipping type? What does it do?
        FliSdk_V2.ImageProcessing.SetColorMap(self.camera_context, -1, "NONE") #TODO: Play around with color maps
        FliSdk_V2.Start(self.camera_context)
        #self.camera_display_loop()
        threading.Thread(target=self.camera_display_loop, daemon=True)
        #self.camera_preview_button.config(state="enabled")
        self.update()

    def camera_display_loop(self):
        while True:
            image = FliSdk_V2.GetProcessedImageRGBANumpyArray(self.camera_context, -1) #-1 to get the last image in the buffer
            img = Image.fromarray(image, mode="RGBA")
            photo = ImageTk.PhotoImage(image=img)
            self.preview.image = photo
            self.preview.configure(image=photo)
            time.sleep(1/self.fps)

    """ def show_image_loop(self, window, image_label):
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
        popup = tk.Toplevel(self)
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
        self.wait_window(popup)  # Wait for popup to close
        FliSdk_V2.Stop(self.camera_context) """

    def select_directory(self):
        dir_path = filedialog.askdirectory()
        #print(f"Selected directory: {dir_path}")
        self.save_dir_text.set(dir_path)
        self.update()

    def scan_module(self): #TODO: Implement this using the variables present in the UI
        self.scan_module_button.config(text="Scanning...", state="disabled")
        buffer_size_images = int(2*self.fps*self.gantry_length/(self.gantry_speed/60))
        FliSdk_V2.SetBufferSizeInImages(self.camera_context, buffer_size_images)
        gantry_utils.scan_continuous(self.gantry_handler,self.camera_context,self.save_dir_text.get(),self.fps,self.gantry_speed)
        print("Not done!")
        

def main():
    root = tk.Tk()
    LIPI_Scanner_App(root).pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()