import sys
import os

fli_path = os.path.abspath(os.path.join(os.getenv('FLISDK_DIR'), "Python/lib"))
if fli_path not in sys.path:
    sys.path.append(fli_path)

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
import tomlkit
import numpy as np
from  PIL import ImageTk, Image
import src.utils.ingaas_processing as ingaas_processing
import src.utils.peripheral_processing as peripheral_processing
import src.stitching.helpers as helpers
import manualStitch
import threading
import time
import datetime
import serial
import winsound
import cv2
import math

import FliSdk_V2

class LIPI_Stitching_App(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ### CONFIG ###
        self.fps = 300
        self.tint = 1 #ms
        self.gain = "Medium"
        self.gantry_speed = 5000 #mm/min
        self.f_mod=50 #Hz
        self.is_modulating=True
        self.gantry_lengthx = 2200
        self.gantry_lengthy = 2100
        self.offset = 100
        #self.drift=0.05622 #new new experimental drift factor
        self.drift = 0
        self.rotation=90 #camera rotation to stitching orientation in degrees

        #p1=self.gantry_lengthx-self.offset
        #self.speedx=p1*self.gantry_speed/(math.sqrt(p1**2+self.gantry_lengthy**2)) #calculation of speed in x and y direction based gantry geometry
        #self.speedy=self.gantry_lengthy*self.gantry_speed/(math.sqrt(p1**2+self.gantry_lengthy**2))    
        self.speedx=4000 #for testing


        ### TKINTER SETUP ###
        parent.protocol("WM_DELETE_WINDOW", self.quit)
        s = ttk.Style()
        s.configure('.', font=('Helvetica', 20))

        my_font = font.Font(family='Helvetica', size=22)
        parent.option_add("*Font", my_font)
 
        # UI ELEMENTS
        #Title text
        # Directory selection
        self.save_dir_frm = ttk.Frame(self)
        tk.Grid.columnconfigure(self.save_dir_frm, 0, weight=1)
        tk.Grid.rowconfigure(self.save_dir_frm, 0, weight=2)
        tk.Grid.rowconfigure(self.save_dir_frm, 1, weight=8)
        self.save_dir_text = tk.StringVar()
        ttk.Label(self, text="File location:").pack()
        ttk.Entry(self.save_dir_frm, textvariable=self.save_dir_text, font=("Helvetica", 18)).grid(row=0, column=0, sticky="nsew")
        ttk.Button(self.save_dir_frm, text="  Select\nDirectory", command=self.select_directory).grid(row=1, column=0, sticky="nsew")
        self.save_dir_frm.pack(fill="both", padx=10, pady=10)
        

        # Scan Type selection
        self.scan_type = tk.StringVar(value="Modulated")
        ttk.Label(self, text="Scan Type:").pack()
        ttk.Combobox(self, textvariable=self.scan_type, values=["Modulated", "Continuous Bias"], state="readonly").pack()

        # Config Menu
        self.config_frm = ttk.LabelFrame(self, text="Configuration")
        self.config_frm.pack(fill="both", padx=10, pady=10)
        
        ttk.Label(self.config_frm, text="FPS (Hz):").grid(row=0, column=0)
        self.fps_var = tk.StringVar(value=str(self.fps))
        ttk.Entry(self.config_frm, textvariable=self.fps_var, width=10).grid(row=0, column=1)

        ttk.Label(self.config_frm, text="Modulation Freq (Hz):").grid(row=1, column=0)
        self.f_mod_var = tk.StringVar(value=str(self.f_mod))
        ttk.Entry(self.config_frm, textvariable=self.f_mod_var, width=10).grid(row=1, column=1)
        
        ttk.Label(self.config_frm, text="Tint (ms):").grid(row=2, column=0)
        self.tint_var = tk.StringVar(value=str(self.tint))
        ttk.Entry(self.config_frm, textvariable=self.tint_var, width=10).grid(row=2, column=1)
        
        ttk.Label(self.config_frm, text="Gain:").grid(row=3, column=0)
        self.gain_var = tk.StringVar(value=self.gain)
        ttk.Combobox(self.config_frm, textvariable=self.gain_var, values=["Low", "Medium", "High"], state="readonly", width=8).grid(row=3, column=1)
        

        # Separate Modulation selection
        ttk.Label(self, text="Separate Modulation:").pack()
        self.separate_modulation = tk.StringVar(value="Yes")
        ttk.Combobox(self, textvariable=self.separate_modulation, values=["Yes", "No"], state="readonly").pack()

        # Start Stitch Button
        self.stitch_button = ttk.Button(self, text="Start Stitch", state="disabled", command=self.start_stitch)
        self.stitch_button.pack(fill="both", padx=10, pady=10)

        # Quit Button
        self.quit_button = ttk.Button(self, text="Quit", command=self.quit)
        self.quit_button.pack(fill="both", padx=10, pady=10)

    def start_stitch(self):

        if self.scan_type.get() == "Modulated":
            n_images = int(self.fps_var.get()) / int(self.f_mod_var.get())  # Change this value to process different numbers of images
            if n_images != int(n_images):
                raise ValueError(f"FPS must be an integer multiple of mod_freq. Current n_images: {n_images}")
            n_images = int(n_images)
            out_path = self.save_dir_text.get()
            if self.separate_modulation.get() == "Yes":
                im_path = filedialog.askopenfilename(initialdir=out_path,title='Select images to process')
                impath_list = manualStitch.separateModulated(im_path, out_path, n=n_images)
            else:
                impath_list = []
                for i in range(n_images):
                    im_path = filedialog.askopenfilename(title=f'Select image {i+1} to process')
                    impath_list.append(im_path)
            cwd=os.getcwd()
            calpath=os.path.join(cwd,"data/calibration")
            print(calpath)
            PLimg_list = []
            PLpath_list = []
            for path in impath_list:
                PLimg, save_path = manualStitch.manualstitch(path,calpath,self.rotation,self.speedx,self.drift,self.fps_var.get())
                PLimg_list.append(PLimg)
                PLpath_list.append(save_path)
            PLpath_list = np.array(PLpath_list)
            
            # Plot intensity line for all images to help user choose which images to use for modulation stitch:
            column_n = 200 
            peripheral_processing.plot_intensity_line(PLpath_list, column_n)
           
            # Get user input for which images to use for modulation stitch:
            first_idx, second_idx = self.get_image_pair(n_images)
            #make sure image sizes are similar, otherwise reduce largest image to size of smallest:
            if PLimg_list[first_idx].shape != PLimg_list[second_idx].shape:
                min_shape = np.minimum(PLimg_list[first_idx].shape, PLimg_list[second_idx].shape)
                PLimg_list[first_idx] = PLimg_list[first_idx][:min_shape[0], :min_shape[1]]
                PLimg_list[second_idx] = PLimg_list[second_idx][:min_shape[0], :min_shape[1]]
                
            modulated_img = PLimg_list[first_idx] - PLimg_list[second_idx]
            cv2.imshow("Modulated Image",ingaas_processing.lin_stretch_img(modulated_img, 1, 99.99))
            cv2.waitKey(0)
            cropped_modulated_img = ingaas_processing.crop_image(modulated_img)
            cv2.imwrite(os.path.join(out_path, "stitched_image_modulated.png"), ingaas_processing.lin_stretch_img(cropped_modulated_img, 1, 99.99))
        else:
            tk.messagebox.showinfo("Not Implemented", "Continuous Bias scan type is not yet implemented.")
            #self.ManualStitch()
            pass
    def get_image_pair(self,n_images):
            dialog = tk.Toplevel(self)
            dialog.title("Select Image Pair")
            dialog.geometry("600x400")
            
            ttk.Label(dialog, text=f"Select two images (0 to {n_images-1}):").pack(pady=10)
            
            ttk.Label(dialog, text="High Bias image:").pack()
            first_var = tk.StringVar()
            ttk.Combobox(dialog, textvariable=first_var, values=list(range(n_images)), state="readonly", width=10).pack()
            
            ttk.Label(dialog, text="Low Bias image:").pack()
            second_var = tk.StringVar()
            ttk.Combobox(dialog, textvariable=second_var, values=list(range(n_images)), state="readonly", width=10).pack()
            
            result = {"first": None, "second": None}
            
            def confirm():
                result["first"] = int(first_var.get())
                result["second"] = int(second_var.get())
                dialog.destroy()
            
            ttk.Button(dialog, text="Confirm and save", command=confirm).pack(pady=10)
            dialog.wait_window()
            
            return result["first"], result["second"]        
    def select_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.save_dir_text.set(dir_path)
        self.update()
    def update(self):
        if str(self.stitch_button["state"]) == "disabled" and self.save_dir_text.get() != "":
            self.stitch_button.config(state="enabled")
        super().update()

def main():
    root = tk.Tk()
    root.title("LIPI Stitching App")
    LIPI_Stitching_App(root).pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()