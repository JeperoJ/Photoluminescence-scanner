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

import sys
import os
fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
import tomlkit as tmlk
import numpy as np
from  PIL import ImageTk, Image
from src import gantry_utils, camera_utils, linescan
import threading
import time
import datetime
import serial
import winsound

import FliSdk_V2


def threaded(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw, daemon=True)
        t.start()
        return t
    return run

class LIPI_Scanner_App(ttk.Frame):
    def __init__(self, parent):
            #Initializing Application Variables
            super().__init__(parent)
            with open("resources/config/default.toml", "r") as f:
                self.config = tmlk.load(f)
            for key in self.config:
                print(key)
                for item in self.config[key]:
                    print(item)



            self.fps = 300
            self.tint = 1
            self.gain = "Medium"


            self.gantry_speed = 5000 #mm/min
            self.f_mod=50 #Hz
            self.is_modulating=True
            #self.fps = self.config["camera"]["fps"]
            #self.tint = self.config["camera"]["tint"]
            #self.gain = self.config["camera"]["gain"]
            #self.gantry_speed = self.config["gantry"]["speed"] #mm/min
            self.gantry_length = 2100 #mm TODO: Add to config (Make proper gantry config)
            #TODO: dpf must be smaller than 1 (dpf calculation from processing)
            #TODO: Check if fps is integer multiple of modulation freq
            #TODO: If modulation do dpf using f_mod
            #TODO: Maybe define speed of gantry using known geometry (dpf=1)
            #TODO: Experiment with making axis move same speed (same distance to move)
            #For axis moving same speed: Both axis should move l=min(l_y, l_x-offset). Command becomes pos(l+offset, l)
            #Thought: At high enough fps, one could modulate to different pumping powers
            #TODO: Seperate UI into more classes. Figure out some proper MVC division. Maybe switch UI package. This file is getting bad.


            self.camera_context = FliSdk_V2.Init()
            self.gantry_handler = None

            self.preview_image = None

            #print(FliSdk_V2.ImageProcessing.GetColorMapList(self.camera_context, -1))

            #UI Appearance
            #parent.attributes('-fullscreen', True)
            parent.protocol("WM_DELETE_WINDOW", quit)
            parent.title("LIPI Scanner")
            s = ttk.Style()
            s.configure('.', font=('Helvetica', 60))

            my_font = font.Font(family='Helvetica', size=32)
            parent.option_add("*Font", my_font)

            #UI Elements

            #Gantry
            com_ports = gantry_utils.get_ports()
            self.gantry_dropdown = ttk.Combobox(self, values=com_ports, state="readonly", postcommand=self.update)
            self.gantry_button = ttk.Button(self, text="Connect Gantry", command=self.connect_gantry)
            #Camera
            FliSdk_V2.DetectGrabbers(self.camera_context)
            self.camera_dropdown = ttk.Combobox(self, values=FliSdk_V2.DetectCameras(self.camera_context), state="readonly", postcommand=lambda: self.camera_dropdown.config(values=FliSdk_V2.DetectCameras(self.camera_context))) #TODO: Improve updating of this, maybe add disconnect
            self.camera_button = ttk.Button(self, text="Connect Camera", command=self.connect_camera)

            self.save_dir_frm = ttk.Frame(self)
            tk.Grid.columnconfigure(self.save_dir_frm, 0, weight=1)
            tk.Grid.rowconfigure(self.save_dir_frm, 0, weight=2)
            tk.Grid.rowconfigure(self.save_dir_frm, 1, weight=8)
            self.save_dir_text = tk.StringVar()
            ttk.Entry(self.save_dir_frm, textvariable=self.save_dir_text, font=("Helvetica", 18)).grid(row=0, column=0, sticky="nsew")
            ttk.Button(self.save_dir_frm, text="  Select\nDirectory", command=self.select_directory).grid(row=1, column=0, sticky="nsew")

            self.button_config = ttk.Button(self, text="Config\n(TBD)", command=self.temp) #TODO: Implement Config Window

            self.preview_frm = ttk.Frame(self)
            self.preview = ttk.Label(self.preview_frm)
            self.preview.pack(fill="both", expand=True)
        
            self.scan_module_button = ttk.Button(self, text="Start\nScan", state="disabled", command=self.scan_module)
            #self.scan_module_button = ttk.Button(self, text="Start\nScan", command=self.temp)

            self.quit_button = ttk.Button(self, text="Quit", command=quit)

            #Organizing UI Elements
            row_weights = [1,5,1,5,5]
            col_weights = [1,1,1,1]
            for i, weight in enumerate(row_weights):
                tk.Grid.rowconfigure(self, i, weight=weight)
            for i, weight in enumerate(col_weights):
                tk.Grid.columnconfigure(self, i, weight=weight)

            padding = 5
            self.gantry_dropdown.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=padding, pady=padding)
            self.gantry_button.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=padding, pady=padding)

            self.camera_dropdown.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=padding, pady=padding)
            self.camera_button.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=padding, pady=padding)

            self.button_config.grid(row=4, column=1, sticky="nsew", padx=padding, pady=padding)
            self.save_dir_frm.grid(row=4, column=0, sticky="nsew", padx=padding, pady=padding)

            self.preview_frm.grid(row=0, column=2, rowspan=4, columnspan=2, sticky="nsew", padx=padding, pady=padding)
            self.scan_module_button.grid(row=4, column=2, sticky="nsew", padx=padding, pady=padding)
            self.quit_button.grid(row=4, column=3, sticky="nsew", padx=padding, pady=padding)

    def temp(self):
        window = tk.Toplevel(self)
        #window.attributes('-fullscreen', True)
        row_weights = [1]
        col_weights = [1, 1]
        for i, weight in enumerate(row_weights):
            tk.Grid.rowconfigure(window, i, weight=weight)
        for i, weight in enumerate(col_weights):
            tk.Grid.columnconfigure(window, i, weight=weight)

        config_options_frame = tk.Frame(window)
        config_options_frame.grid(row=0, column=0, sticky="nsew")

        config_extra_frame = ttk.Frame(window)
        config_extra_frame.grid(row=0, column=1, sticky="nsew")




    def update(self):
        self.com_ports = gantry_utils.get_ports()
        self.gantry_dropdown.config(values=self.com_ports)
        if str(self.camera_button["state"]) == "disabled" and str(self.gantry_button["state"]) == "disabled" and self.save_dir_text.get() != "" and str(self.scan_module_button["text"])=="Start\nScan":
            self.scan_module_button.config(state="enabled")

        super().update()

    def quit(self):
        camera_utils.disconnect(self.camera_context)
        if self.gantry_handler is not None:
            self.gantry_handler.disconnect()

        super().quit()

    def popup(self, title, text, dismiss=False, sound=False):
        popup = tk.Toplevel(self)
        popup.title(title)
        #popup.geometry("600x200")
        popup.grab_set()  # Make modal, locks root window
        ttk.Label(popup, text=text).pack(pady=10)
        popup.update()
        if sound:
            winsound.Beep(2500, 1000)
        if dismiss:
            ttk.Button(popup, text="OK", command=popup.destroy).pack()
            self.wait_window(popup)  # Wait for popup to close
        if not dismiss:
            return popup

    #Gantry
    def connect_gantry(self):
        if self.gantry_dropdown.get() == "":
            self.popup("Gantry Connection", "No gantry port selected!", dismiss=True)
            return
        _popup = self.popup("Gantry Connection", "Connecting to gantry_utils. Please wait...")
        try:
            self.gantry_handler = gantry_utils.connect(self.com_ports[[str(port) for port in self.com_ports].index(self.gantry_dropdown.get())])
        except (TimeoutError,serial.SerialException) as e:
            _popup.destroy()
            print(e)
            self.popup("Gantry Connection", "Connection failed. Check that the board is connected and powered, or try a different port.", dismiss=True, sound = True)
            return
        except Exception as e:
            _popup.destroy()
            print(e)
            self.popup("Gantry Connection", "Connection failed for unknown reason. Check that everything is correctly setup.", dismiss=True, sound=True)
            return

        self.gantry_button.config(text="Calibrate Gantry", command=self.calibrate_gantry)
        self.gantry_dropdown.config(state="disabled")
        _popup.destroy()
        self.update()

    def calibrate_gantry(self):
        self.popup("Gantry Calibration", "Please make sure the gantry area is clear and press OK to continue.", dismiss=True)
        _popup = self.popup("Gantry Calibration", "Calibrating gantry_utils. Please wait...")

        try:
            gantry_utils.calibrate(self.gantry_handler)
        except TimeoutError as e:
            _popup.destroy()
            print(e)
            self.popup("Gantry Calibration", "Gantry calibration timed out. Ensure that emergency stop is not triggered.", dismiss=True, sound=True)
        except Exception as e:
            _popup.destroy()
            print(e)
            self.popup("Gantry Calibration", "Unknown error during gantry calibration.", dismiss=True, sound=True)

        self.gantry_button.config(text="Gantry Ready", state="disabled")
        _popup.destroy()
        self.update()

    #Camera
    def connect_camera(self):
        if self.camera_dropdown.get() == "":
            self.popup("Camera Connection", "No camera selected!", dismiss=True)
            return
        _popup = self.popup("Camera Initialization", "Connecting to camera. Please wait...")
        try:
            camera_utils.init_camera(self.camera_context, self.fps, self.tint, self.camera_dropdown.get(), gain=self.gain)
        except Exception as e:
            _popup.destroy()
            print(e)
            self.popup("Camera Connection", "Connection Failed. Check that the camera is connected and powered, or try a different option.", dismiss=True)
            return
        self.camera_button.config(text="Calibrate", command=self.calibrate_camera)
        self.camera_dropdown.config(state="disabled")
        _popup.destroy()
        self.update()

    def calibrate_camera(self):
        self.popup("Camera Calibration", "Please put on the camera lens cap and press OK to continue.", dismiss=True)
        _popup = self.popup("Camera Calibration", "Calibrating camera. Please wait...")
        _popup.update()
        try:
           camera_utils.calibrate_camera(self.camera_context, adaptiveBias=False)
        except Exception as e:
           _popup.destroy()
           print(e)
           self.popup("Camera Calibration", "Calibration Failed. No idea why. Check terminal output and consider pulling the power.", dismiss=True, sound=True)
        self.camera_button.config(text="Camera Ready", state="disabled")
        _popup.destroy()
        #FliSdk_V2.ImageProcessing.EnableAutoClip(self.camera_context, -1, True) #TODO: Clipping type? What does it do?
        FliSdk_V2.ImageProcessing.SetColorMap(self.camera_context, -1, "NONE") #TODO: Play around with color maps
        FliSdk_V2.Start(self.camera_context)
        self.process_preview()
        self.display_preview(self.preview)
        self.update()

    #@threaded
    @threaded
    def process_preview(self):
        #Threaded processing script so it does not block the main(ui) thread. Uses time to not do this constantly. Might be better way.
        #TODO: Add stretching of the image irt. contrast. Should not be a problem now it is in a separate thread.
        timestamp = time.perf_counter_ns()
        while True:
            if FliSdk_V2.IsStarted(self.camera_context) and (time.perf_counter_ns() - timestamp > 10 ** 9 / self.fps): #Only run if enough time elapsed and the SDK is capturing.
                image = np.array(FliSdk_V2.GetProcessedImageRGBANumpyArray(self.camera_context, -1))  # -1 to get the last image in the buffer. np.array wrap to make sure it is newest version (Dont know if needed just have experienced issues before)
                #Any image processing goes here. Into new object, and pass that into the fromarray
                photo = ImageTk.PhotoImage(image=Image.fromarray(image)) #Take array, into PIL image, into image usable in tk. Have no idea if this can be improved
                self.preview_image = photo #Sets class variable, so it can be fetched by display_preview
                timestamp = time.perf_counter_ns()
            else:
                time.sleep(1E-2)

    def display_preview(self, label):
        image = self.preview_image #Capture current stored image, so if it changes during it should not impact this function.
        label.image = image #Sets it in the label the first time
        label.configure(image=image) #Sets it in the label the second time. Need both lines else weird stuff happens. No clue why but I have accepted it.
        self.after(20, self.display_preview, label) #Run this at 50 hz ish, minus processing time or any blocking of the main thread.

    # def camera_display_loop(self):
    #     #print(FliSdk_V2.IsStarted(self.camera_context))
    #     if FliSdk_V2.IsStarted(self.camera_context):
    #         image = np.array(FliSdk_V2.GetProcessedImageRGBANumpyArray(self.camera_context, -1)) #-1 to get the last image in the buffer
    #         img = Image.fromarray(image, mode="RGBA")
    #         photo = ImageTk.PhotoImage(image=img)
    #         self.preview.image = photo
    #         self.preview.configure(image=photo)
    #         self.preview.update()
    #     self.after(20, self.camera_display_loop)

    def select_directory(self):
        dir_path = filedialog.askdirectory()
        #print(f"Selected directory: {dir_path}")
        self.save_dir_text.set(dir_path)
        self.update()

    def scan_module(self): #TODO: Implement this using the variables present in the UI
        self.popup("Scanning",
                   """Verify that:
                       -Camera cover is off
                       -Lightbar is on
                       -Scanner area is clear
                   Scanning will proceed when \"OK\" is pressed.""",
                   dismiss=True, sound=True)
        self.scan_module_button.config(text="Scanning...", state="disabled")
        for child in self.save_dir_frm.winfo_children():
            child.configure(state="disabled")
        self.update()
        buffer_size_images = int(2*self.fps*self.gantry_length/(self.gantry_speed/60))
        print(f"Buffer size images: {buffer_size_images}")
        FliSdk_V2.SetBufferSizeInImages(self.camera_context, buffer_size_images)
        #FliSdk_V2.SetBufferSize(self.camera_context, buffer_size_images)
        print(f"Context buffer size: {FliSdk_V2.GetImagesCapacity(self.camera_context)}")
        #gantry_utils.scan_continuous(self.gantry_handler,self.camera_context,self.save_dir_text.get(),self.fps,self.gantry_speed)
        t = threading.Thread(target=self.scan_thread, daemon=True)
        t.start()

    def scan_thread(self):
        linescan.continuous(self.gantry_handler, self.camera_context, self.save_dir_text.get(), self.fps,
                            self.gantry_speed)
        self.after(0, self.scan_module_button.config, "Scanned")
        # self.scan_module_button.config(text="Reset\nGantry", state="enabled", command=self.reset)
        self.after(0, self.popup, "Scanning", "Scan completed. Turn off lighbar.", True, True)

    """ def reset(self):
        self.scan_module_button.config(text="Resetting...", state="disabled")
        self.update()
        self.gantry_handler """
        

def main():
    root = tk.Tk()
    LIPI_Scanner_App(root).pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()