import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import datetime
sys.path.append('FLI_API')
sys.path.append('Stitching')
sys.path.append('Acquisition')
sys.path.append('lib')

from lib import ProcessInGaAs
from lib import imageAcquisition
from lib import gCodeHandler
from lib import stitchImages
import tifffile
from FLI_API import FliSdk_V2


class PLScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PL Scanner Control System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # System state variables
        self.context = None
        self.gcode_handler = None
        self.K = None
        self.P = None
        self.DIM = None
        self.cwd = os.getcwd()
        
        # Configuration variables
        self.speed = tk.IntVar(value=5000)
        self.frameRate = tk.IntVar(value=50)
        self.tintVal = tk.IntVar(value=1)
        self.nsteps = tk.IntVar(value=3)
        self.drift = tk.DoubleVar(value=0.2448)
        self.calpath = tk.StringVar(value=os.path.join(self.cwd, "Calibration"))
        
        # Status variables
        self.camera_connected = tk.BooleanVar(value=False)
        self.gantry_connected = tk.BooleanVar(value=False)
        self.calibration_loaded = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.scan_tab = ttk.Frame(self.notebook)
        self.process_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.setup_tab, text="Setup & Calibration")
        self.notebook.add(self.scan_tab, text="Scanning")
        self.notebook.add(self.process_tab, text="Processing")
        
        # Setup each tab
        self.create_setup_tab()
        self.create_scan_tab()
        self.create_process_tab()
        
        # Create status bar at bottom
        self.create_status_bar()
        
    def create_setup_tab(self):
        """Create the setup and calibration tab"""
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.setup_tab, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Speed
        ttk.Label(config_frame, text="Speed (mm/min):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.speed, width=15).grid(row=0, column=1, pady=2)
        
        # Frame Rate
        ttk.Label(config_frame, text="Frame Rate (FPS):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.frameRate, width=15).grid(row=1, column=1, pady=2)
        
        # Exposure
        ttk.Label(config_frame, text="Exposure (ms):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.tintVal, width=15).grid(row=2, column=1, pady=2)
        
        # Steps
        ttk.Label(config_frame, text="Number of Steps:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.nsteps, width=15).grid(row=3, column=1, pady=2)
        
        # Drift
        ttk.Label(config_frame, text="Drift (mm/step):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.drift, width=15).grid(row=4, column=1, pady=2)
        
        # Calibration Frame
        cal_frame = ttk.LabelFrame(self.setup_tab, text="Calibration", padding=10)
        cal_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Calibration path
        ttk.Label(cal_frame, text="Calibration Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(cal_frame, textvariable=self.calpath, width=40).grid(row=0, column=1, pady=2, padx=5)
        ttk.Button(cal_frame, text="Browse", command=self.browse_calibration).grid(row=0, column=2, pady=2)
        
        ttk.Button(cal_frame, text="Load Calibration", command=self.load_calibration).grid(row=1, column=0, columnspan=3, pady=5)
        
        # Camera Frame
        camera_frame = ttk.LabelFrame(self.setup_tab, text="Camera Setup", padding=10)
        camera_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.camera_status_label = ttk.Label(camera_frame, text="Status: Not Connected", foreground="red")
        self.camera_status_label.pack(pady=5)
        
        btn_frame = ttk.Frame(camera_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Initialize Camera", command=self.initialize_camera).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Disconnect Camera", command=self.disconnect_camera).pack(side=tk.LEFT, padx=5)
        
        # Gantry Frame
        gantry_frame = ttk.LabelFrame(self.setup_tab, text="Gantry Setup", padding=10)
        gantry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.gantry_status_label = ttk.Label(gantry_frame, text="Status: Not Connected", foreground="red")
        self.gantry_status_label.pack(pady=5)
        
        btn_frame2 = ttk.Frame(gantry_frame)
        btn_frame2.pack(pady=5)
        
        ttk.Button(btn_frame2, text="Connect Gantry", command=self.connect_gantry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Home Gantry", command=self.home_gantry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Disconnect Gantry", command=self.disconnect_gantry).pack(side=tk.LEFT, padx=5)
        
    def create_scan_tab(self):
        """Create the scanning tab"""
        # Scan type selection
        scan_frame = ttk.LabelFrame(self.scan_tab, text="Scan Type", padding=10)
        scan_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.scan_type = tk.StringVar(value="multi")
        ttk.Radiobutton(scan_frame, text="Multi-Step Scan (3 positions)", variable=self.scan_type, 
                       value="multi").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(scan_frame, text="Continuous Scan", variable=self.scan_type, 
                       value="continuous").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(scan_frame, text="EL Scan (Experimental)", variable=self.scan_type, 
                       value="el").pack(anchor=tk.W, pady=2)
        
        # Scan control
        control_frame = ttk.LabelFrame(self.scan_tab, text="Scan Control", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(control_frame, text="?? Before scanning:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        ttk.Label(control_frame, text="� Place PV panel under light source").pack(anchor=tk.W, padx=20)
        ttk.Label(control_frame, text="� Turn on light source").pack(anchor=tk.W, padx=20)
        ttk.Label(control_frame, text="� Remove camera cover").pack(anchor=tk.W, padx=20)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=10)
        
        self.start_scan_btn = ttk.Button(btn_frame, text="Start Scan", command=self.start_scan, 
                                         style="Accent.TButton")
        self.start_scan_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Emergency Stop", command=self.emergency_stop, 
                  style="Danger.TButton").pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_frame = ttk.LabelFrame(self.scan_tab, text="Scan Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.scan_log = scrolledtext.ScrolledText(progress_frame, height=15, wrap=tk.WORD)
        self.scan_log.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def create_process_tab(self):
        """Create the processing tab"""
        # File selection
        file_frame = ttk.LabelFrame(self.process_tab, text="Image Selection", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="Image Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.image_dir = tk.StringVar(value=os.path.join(self.cwd, "Images"))
        ttk.Entry(file_frame, textvariable=self.image_dir, width=50).grid(row=0, column=1, pady=2, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_images).grid(row=0, column=2, pady=2)
        
        # Processing options
        process_frame = ttk.LabelFrame(self.process_tab, text="Processing Options", padding=10)
        process_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.process_type = tk.StringVar(value="auto")
        ttk.Radiobutton(process_frame, text="Auto-detect scan type", variable=self.process_type, 
                       value="auto").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(process_frame, text="Process as multi-step scan", variable=self.process_type, 
                       value="multi").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(process_frame, text="Process as continuous scan", variable=self.process_type, 
                       value="continuous").pack(anchor=tk.W, pady=2)
        
        ttk.Button(process_frame, text="Start Processing", command=self.start_processing).pack(pady=10)
        
        # Processing log
        log_frame = ttk.LabelFrame(self.process_tab, text="Processing Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.process_log = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.process_log.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def create_status_bar(self):
        """Create status bar at bottom of window"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Status indicators
        self.cal_indicator = ttk.Label(status_frame, text="? Cal", foreground="gray")
        self.cal_indicator.pack(side=tk.RIGHT, padx=5)
        
        self.gantry_indicator = ttk.Label(status_frame, text="? Gantry", foreground="gray")
        self.gantry_indicator.pack(side=tk.RIGHT, padx=5)
        
        self.camera_indicator = ttk.Label(status_frame, text="? Camera", foreground="gray")
        self.camera_indicator.pack(side=tk.RIGHT, padx=5)
        
    # Callback methods
    def browse_calibration(self):
        """Browse for calibration directory"""
        directory = filedialog.askdirectory(initialdir=self.calpath.get())
        if directory:
            self.calpath.set(directory)
            
    def browse_images(self):
        """Browse for image directory"""
        directory = filedialog.askdirectory(initialdir=self.image_dir.get())
        if directory:
            self.image_dir.set(directory)
            
    def load_calibration(self):
        """Load calibration files"""
        try:
            self.log_message("Loading calibration from: " + self.calpath.get())
            self.K, self.P, self.DIM = ProcessInGaAs.loadCal(self.calpath.get(), 640, 512)
            self.calibration_loaded.set(True)
            self.cal_indicator.config(text="?? Cal", foreground="green")
            self.log_message("? Calibration loaded successfully")
            messagebox.showinfo("Success", "Calibration loaded successfully!")
        except Exception as e:
            self.log_message(f"? Error loading calibration: {str(e)}")
            messagebox.showerror("Error", f"Failed to load calibration:\n{str(e)}")
            
    def initialize_camera(self):
        """Initialize camera with user-selected options"""
        def init_thread():
            try:
                self.log_message("Initializing camera...")
                self.context = FliSdk_V2.Init()
                imageAcquisition.initCamera(self.context, self.frameRate.get(), self.tintVal.get())
                imageAcquisition.PixelCorrect(self.context, True)
                
                # Ask user for bias correction options
                self.root.after(0, self.ask_bias_correction)
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"? Error initializing camera: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to initialize camera:\n{str(e)}"))
                
        threading.Thread(target=init_thread, daemon=True).start()
        
    def ask_bias_correction(self):
        """Ask user about bias correction preferences"""
        result = messagebox.askyesno("Bias Correction", "Build standard NUC bias?")
        
        if result:
            try:
                imageAcquisition.BuildNUCBias(self.context)
                self.log_message("? NUC bias built")
                
                adaptive = messagebox.askyesno("Adaptive Bias", "Also enable Adaptive Bias?")
                if adaptive:
                    imageAcquisition.EnableAdaptBias(self.context)
                    self.log_message("? Adaptive bias enabled")
            except Exception as e:
                self.log_message(f"? Error with bias correction: {str(e)}")
        else:
            adaptive = messagebox.askyesno("Adaptive Bias", "Enable Adaptive Bias instead?")
            if adaptive:
                try:
                    imageAcquisition.EnableAdaptBias(self.context)
                    self.log_message("? Adaptive bias enabled")
                except Exception as e:
                    self.log_message(f"? Error enabling adaptive bias: {str(e)}")
        
        # Enable anti-blooming and auto-clip
        try:
            FliSdk_V2.FliCredThree.EnableAntiBlooming(self.context, True)
            self.log_message("? Anti-blooming enabled")
            FliSdk_V2.ImageProcessing.EnableAutoClip(self.context, -1, True)
            self.log_message("? Auto clip enabled")
            
            self.camera_connected.set(True)
            self.camera_status_label.config(text="Status: Connected", foreground="green")
            self.camera_indicator.config(text="?? Camera", foreground="green")
            self.log_message("? Camera initialized successfully")
            messagebox.showinfo("Success", "Camera initialized successfully!")
        except Exception as e:
            self.log_message(f"? Error enabling camera features: {str(e)}")
            
    def disconnect_camera(self):
        """Disconnect camera"""
        try:
            if self.context:
                FliSdk_V2.Stop(self.context)
                FliSdk_V2.Exit(self.context)
                self.context = None
                self.camera_connected.set(False)
                self.camera_status_label.config(text="Status: Not Connected", foreground="red")
                self.camera_indicator.config(text="? Camera", foreground="gray")
                self.log_message("? Camera disconnected")
        except Exception as e:
            self.log_message(f"? Error disconnecting camera: {str(e)}")
            
    def connect_gantry(self):
        """Connect to gantry"""
        def connect_thread():
            try:
                available_ports = gCodeHandler.get_available_ports()
                
                if not available_ports:
                    self.root.after(0, lambda: messagebox.showerror("Error", "No serial ports found!"))
                    return
                
                # Create dialog to select port
                self.root.after(0, lambda: self.show_port_selection(available_ports))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"? Error connecting to gantry: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to connect:\n{str(e)}"))
                
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def show_port_selection(self, available_ports):
        """Show dialog to select serial port"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Serial Port")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Select the gantry serial port:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for port in available_ports:
            listbox.insert(tk.END, f"{port.device} - {port.description}")
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                port = available_ports[selection[0]].device
                dialog.destroy()
                self.connect_to_port(port)
            else:
                messagebox.showwarning("Warning", "Please select a port")
        
        ttk.Button(dialog, text="Connect", command=on_select).pack(pady=10)
        
    def connect_to_port(self, port):
        """Connect to selected port"""
        def connect_thread():
            try:
                self.log_message(f"Connecting to port: {port}")
                self.gcode_handler = gCodeHandler.GCodeHandler(port)
                self.gcode_handler.connect()
                
                self.root.after(0, lambda: self.gantry_connected.set(True))
                self.root.after(0, lambda: self.gantry_status_label.config(text="Status: Connected", foreground="green"))
                self.root.after(0, lambda: self.gantry_indicator.config(text="?? Gantry", foreground="green"))
                self.root.after(0, lambda: self.log_message("? Gantry connected successfully"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Gantry connected successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"? Error connecting to port: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to connect:\n{str(e)}"))
                
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def home_gantry(self):
        """Home the gantry"""
        if not self.gantry_connected.get():
            messagebox.showwarning("Warning", "Gantry not connected!")
            return
            
        def home_thread():
            try:
                self.log_message("Checking end stops...")
                endStop = ["M120", "M119"]
                t = self.gcode_handler.send_gcode(endStop)
                
                count = 0
                while any("TRIGGERED" in line for line in t) and count < 2:
                    axis_trig = []
                    for line in t:
                        if "TRIGGERED" in line:
                            axis = line.split("_")[0]
                            axis_trig.append(axis)
                    
                    self.root.after(0, lambda a=axis_trig: self.log_message(f"End stop triggered: {', '.join(a)}. Moving away..."))
                    
                    if axis in ['x', 'x2']:
                        self.gcode_handler.send_gcode("G0 X30")
                        self.gcode_handler.wait()
                    elif axis in ['y', 'y2']:
                        self.gcode_handler.send_gcode("G0 Y30")
                        self.gcode_handler.wait()
                    
                    t = self.gcode_handler.send_gcode("M119")
                    count += 1
                
                self.root.after(0, lambda: self.log_message("Homing gantry..."))
                self.gcode_handler.auto_home()
                self.gcode_handler.wait()
                
                self.root.after(0, lambda: self.log_message("? Gantry homed successfully"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Gantry homed successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"? Error homing gantry: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to home gantry:\n{str(e)}"))
                
        threading.Thread(target=home_thread, daemon=True).start()
        
    def disconnect_gantry(self):
        """Disconnect gantry"""
        try:
            if self.gcode_handler:
                self.gcode_handler.disconnect()
                self.gcode_handler = None
                self.gantry_connected.set(False)
                self.gantry_status_label.config(text="Status: Not Connected", foreground="red")
                self.gantry_indicator.config(text="? Gantry", foreground="gray")
                self.log_message("? Gantry disconnected")
        except Exception as e:
            self.log_message(f"? Error disconnecting gantry: {str(e)}")
            
    def start_scan(self):
        """Start scanning process"""
        if not self.camera_connected.get():
            messagebox.showwarning("Warning", "Camera not connected!")
            return
        if not self.gantry_connected.get():
            messagebox.showwarning("Warning", "Gantry not connected!")
            return
        if not self.calibration_loaded.get():
            messagebox.showwarning("Warning", "Calibration not loaded!")
            return
            
        scan_type = self.scan_type.get()
        
        # Confirm scan start
        result = messagebox.askyesno("Start Scan", 
                                     "Ready to start scan?\n\n" +
                                     "Make sure:\n" +
                                     "� PV panel is positioned\n" +
                                     "� Light source is ON\n" +
                                     "� Camera cover is removed")
        if not result:
            return
            
        def scan_thread():
            try:
                self.root.after(0, lambda: self.start_scan_btn.config(state='disabled'))
                self.root.after(0, lambda: self.log_scan(f"Starting {scan_type} scan..."))
                
                savePath = os.path.join(self.cwd, "Images")
                os.makedirs(savePath, exist_ok=True)
                
                if scan_type == "multi":
                    self.run_multi_scan(savePath)
                elif scan_type == "continuous":
                    self.run_continuous_scan(savePath)
                elif scan_type == "el":
                    self.run_el_scan(savePath)
                
                self.root.after(0, lambda: self.log_scan("? Scan completed successfully!"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Scan completed successfully!"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_scan(f"? Error during scan: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Scan failed:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self.start_scan_btn.config(state='normal'))
                self.root.after(0, lambda: self.progress_var.set(0))
                
        threading.Thread(target=scan_thread, daemon=True).start()
        
    def run_multi_scan(self, savePath):
        """Run multi-step scan"""
        from PLRobot import scan
        scan(self.gcode_handler, self.context, savePath, self.frameRate.get(), 
             self.speed.get(), self.nsteps.get())
        
    def run_continuous_scan(self, savePath):
        """Run continuous scan"""
        from PLRobot import scanContinuous
        scanContinuous(self.gcode_handler, self.context, savePath, 
                      self.frameRate.get(), self.speed.get())
        
    def run_el_scan(self, savePath):
        """Run EL scan"""
        from PLRobot import scanEL
        scanEL(self.gcode_handler, self.context, savePath, 
               self.frameRate.get(), self.speed.get())
        
    def emergency_stop(self):
        """Emergency stop all operations"""
        result = messagebox.askyesno("Emergency Stop", "Stop all operations immediately?")
        if result:
            try:
                if self.gcode_handler:
                    self.gcode_handler.send_gcode("M112")  # Emergency stop
                if self.context:
                    FliSdk_V2.Stop(self.context)
                self.log_scan("?? EMERGENCY STOP activated")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to execute emergency stop:\n{str(e)}")
                
    def start_processing(self):
        """Start image processing"""
        if not self.calibration_loaded.get():
            messagebox.showwarning("Warning", "Calibration not loaded!")
            return
            
        def process_thread():
            try:
                self.root.after(0, lambda: self.log_process("Starting image processing..."))
                
                image_dir = self.image_dir.get()
                process_type = self.process_type.get()
                
                # Get image files
                image_files = [f for f in os.listdir(image_dir) 
                             if f.endswith('.raw') or f.endswith('.tiff')]
                
                if not image_files:
                    self.root.after(0, lambda: messagebox.showwarning("Warning", "No image files found!"))
                    return
                
                # Auto-detect or use specified type
                if process_type == "auto":
                    if any('scan_cont' in f for f in image_files):
                        process_type = "continuous"
                    else:
                        process_type = "multi"
                
                self.root.after(0, lambda: self.log_process(f"Processing as {process_type} scan..."))
                
                if process_type == "multi":
                    self.process_multi_scan(image_dir, image_files)
                elif process_type == "continuous":
                    self.process_continuous_scan(image_dir, image_files)
                
                self.root.after(0, lambda: self.log_process("? Processing completed successfully!"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Processing completed!"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_process(f"? Error during processing: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed:\n{str(e)}"))
                
        threading.Thread(target=process_thread, daemon=True).start()
        
    def process_multi_scan(self, image_dir, image_files):
        """Process multi-step scan images"""
        from PLRobot import stitch
        
        for image_file in image_files:
            self.root.after(0, lambda f=image_file: self.log_process(f"Processing {f}..."))
            image_path = os.path.join(image_dir, image_file)
            stitch(image_path, self.K, self.P, self.DIM, "1")
        
        # Multi-stitch
        GeoPLstitched_images = [os.path.join(image_dir, f) for f in os.listdir(image_dir) 
                               if f.endswith('GeoPL_stitched.png')]
        if GeoPLstitched_images:
            self.root.after(0, lambda: self.log_process("Creating final multi-stitch..."))
            stitchImages.multiStitch(GeoPLstitched_images)
        
    def process_continuous_scan(self, image_dir, image_files):
        """Process continuous scan images"""
        scan_files = [f for f in image_files if 'scan_cont' in f]
        if not scan_files:
            raise ValueError("No continuous scan files found")
        
        latest_image_file = max([os.path.join(image_dir, f) for f in scan_files], 
                              key=os.path.getctime)
        
        self.root.after(0, lambda: self.log_process(f"Processing {os.path.basename(latest_image_file)}..."))
        
        images = tifffile.imread(latest_image_file)
        stitchImages.roughStitchCont(images, self.K, self.P, self.DIM, latest_image_file,
                                    self.speed.get(), self.nsteps.get(), self.frameRate.get(),
                                    savename="stitched_image_cont.png", drift=self.drift.get())
        
    def log_message(self, message):
        """Log message to status bar"""
        self.status_label.config(text=message)
        print(message)
        
    def log_scan(self, message):
        """Log message to scan log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.scan_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.scan_log.see(tk.END)
        print(message)
        
    def log_process(self, message):
        """Log message to process log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.process_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.process_log.see(tk.END)
        print(message)


def main():
    root = tk.Tk()
    
    # Set theme style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Custom button styles
    style.configure("Accent.TButton", foreground="white", background="#0066cc", 
                   font=('Arial', 10, 'bold'))
    style.configure("Danger.TButton", foreground="white", background="#cc0000",
                   font=('Arial', 10, 'bold'))
    
    app = PLScannerGUI(root)
    
    # Handle window close
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                if app.context:
                    FliSdk_V2.Stop(app.context)
                    FliSdk_V2.Exit(app.context)
                if app.gcode_handler:
                    app.gcode_handler.disconnect()
            except:
                pass
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
