"""
Configuration UI using MVC paradigm.
- Model: Handles config data storage and validation
- View: Displays the UI
- Controller: Manages interactions between Model and View
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np


class ConfigModel:
    """Model: Holds and manages configuration data"""
    
    def __init__(self, config_dict=None):
        self.config = config_dict or {
            "general": {
                "dpf": 0.33,
            },
            "lightbar": {
                "intensity": 1,
                "modulation": True,
                "freq": 0,
                "duty_cycle": 60,
                "waveform": "Square",
            },
            "gantry": {
                "speed": 5000,
                "length_x": 2100,
                "length_y": 2000,
                "offset": 200,
                "cam_height": 1000,
            },
            "camera": {
                "fps": 50,
                "fps_ratio": 6,
                "exposure": 1,
                "gain": "Medium",
            },
        }
        self.callbacks = []
    
    def get(self, section, key):
        """Get a config value"""
        return self.config.get(section, {}).get(key)
    
    def set(self, section, key, value):
        """Set a config value and notify callbacks"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._notify_callbacks()
    
    def get_section(self, section):
        """Get entire section"""
        return self.config.get(section, {})
    
    def subscribe(self, callback):
        """Subscribe to config changes"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all subscribers of changes"""
        for callback in self.callbacks:
            callback(self.config)


class ConfigView:
    """View: Displays the configuration UI"""
    
    def __init__(self, parent, model, controller):
        self.model = model
        self.controller = controller
        self.widgets = {}
        
        self.window = tk.Toplevel(parent)
        self.window.title("Scanner Configuration")
        self.window.geometry("800x600")
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the main UI structure"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_general_tab()
        self._create_lightbar_tab()
        self._create_gantry_tab()
        self._create_camera_tab()
        
        # Create bottom buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply", command=self.controller.apply_config).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.controller.reset_defaults).pack(side="right", padx=5)
    
    def _create_general_tab(self):
        """Create General tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="General")
        
        self._add_labeled_entry(tab, "Distance Per Frame (pixels)", "general", "dpf", 0)
    
    def _create_lightbar_tab(self):
        """Create Lightbar tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Lightbar")
        
        row = 0
        self._add_labeled_entry(tab, "Intensity", "lightbar", "intensity", row)
        row += 1
        self._add_labeled_checkbox(tab, "Modulation Enabled", "lightbar", "modulation", row)
        row += 1
        self._add_labeled_entry(tab, "Frequency (Hz)", "lightbar", "freq", row)
        row += 1
        self._add_labeled_entry(tab, "Duty Cycle (%)", "lightbar", "duty_cycle", row)
        row += 1
        self._add_labeled_combo(tab, "Waveform", "lightbar", "waveform", ["Square", "Sine", "Triangle"], row)
    
    def _create_gantry_tab(self):
        """Create Gantry tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Gantry")
        
        row = 0
        self._add_labeled_entry(tab, "Speed (mm/min)", "gantry", "speed", row)
        row += 1
        self._add_labeled_entry(tab, "Length X (mm)", "gantry", "length_x", row)
        row += 1
        self._add_labeled_entry(tab, "Length Y (mm)", "gantry", "length_y", row)
        row += 1
        self._add_labeled_entry(tab, "Offset (mm)", "gantry", "offset", row)
        row += 1
        self._add_labeled_entry(tab, "Camera Height (mm)", "gantry", "cam_height", row)
    
    def _create_camera_tab(self):
        """Create Camera tab with preview"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Camera")
        
        # Create two columns: settings on left, preview on right
        settings_frame = ttk.Frame(tab)
        settings_frame.pack(side="left", fill="both", expand=False, padx=10, pady=10)
        
        preview_frame = ttk.Frame(tab)
        preview_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Settings in settings_frame
        ttk.Label(settings_frame, text="Camera Settings", font=("Helvetica", 12, "bold")).pack(anchor="w")
        
        row = 0
        self._add_labeled_entry(settings_frame, "FPS", "camera", "fps", row)
        row += 1
        self._add_labeled_entry(settings_frame, "FPS Ratio", "camera", "fps_ratio", row)
        row += 1
        self._add_labeled_entry(settings_frame, "Exposure (ms)", "camera", "exposure", row)
        row += 1
        self._add_labeled_combo(settings_frame, "Gain", "camera", "gain", ["Low", "Medium", "High"], row)
        
        # Preview in preview_frame
        ttk.Label(preview_frame, text="Camera Preview", font=("Helvetica", 12, "bold")).pack(anchor="w")
        
        self.preview_label = ttk.Label(preview_frame, text="[Preview will appear here]", relief="sunken", background="#222222")
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _add_labeled_entry(self, parent, label_text, section, key, row):
        """Add a labeled entry field"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", pady=5)
        
        var = tk.StringVar(value=str(self.model.get(section, key)))
        entry = ttk.Entry(parent, textvariable=var, width=20)
        entry.grid(row=row, column=1, sticky="ew", pady=5)
        
        # Store reference
        widget_key = f"{section}_{key}"
        self.widgets[widget_key] = (entry, var, section, key, "entry")
        
        parent.columnconfigure(1, weight=1)
    
    def _add_labeled_checkbox(self, parent, label_text, section, key, row):
        """Add a labeled checkbox"""
        var = tk.BooleanVar(value=self.model.get(section, key))
        checkbox = ttk.Checkbutton(parent, text=label_text, variable=var)
        checkbox.grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        
        # Store reference
        widget_key = f"{section}_{key}"
        self.widgets[widget_key] = (checkbox, var, section, key, "checkbox")
    
    def _add_labeled_combo(self, parent, label_text, section, key, options, row):
        """Add a labeled combobox"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky="w", pady=5)
        
        var = tk.StringVar(value=str(self.model.get(section, key)))
        combo = ttk.Combobox(parent, textvariable=var, values=options, state="readonly", width=17)
        combo.grid(row=row, column=1, sticky="ew", pady=5)
        
        # Store reference
        widget_key = f"{section}_{key}"
        self.widgets[widget_key] = (combo, var, section, key, "combo")
        
        parent.columnconfigure(1, weight=1)
    
    def get_values(self):
        """Get all current values from widgets"""
        values = {}
        for widget_key, (widget, var, section, key, widget_type) in self.widgets.items():
            if section not in values:
                values[section] = {}
            
            if widget_type == "checkbox":
                values[section][key] = var.get()
            elif widget_type in ["entry", "combo"]:
                raw_value = var.get()
                # Try to convert to appropriate type
                try:
                    if isinstance(self.model.get(section, key), (int, float)):
                        if isinstance(self.model.get(section, key), int):
                            values[section][key] = int(raw_value)
                        else:
                            values[section][key] = float(raw_value)
                    else:
                        values[section][key] = raw_value
                except ValueError:
                    values[section][key] = raw_value
        
        return values
    
    def update_preview(self, image_array=None):
        """Update the camera preview display"""
        if image_array is not None:
            # Convert numpy array to PhotoImage
            image = Image.fromarray(image_array)
            # Resize to fit preview area
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
        else:
            self.preview_label.configure(text="[No preview available]")


class ConfigController:
    """Controller: Manages interactions between Model and View"""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
    
    def apply_config(self):
        """Apply configuration changes"""
        values = self.view.get_values()
        for section, section_values in values.items():
            for key, value in section_values.items():
                self.model.set(section, key, value)
        print("Configuration applied:", self.model.config)
        self.view.window.destroy()
    
    def reset_defaults(self):
        """Reset to default values"""
        # Recreate config with defaults
        self.model.config = {
            "general": {"dpf": 0.33},
            "lightbar": {
                "intensity": 1,
                "modulation": True,
                "freq": 0,
                "duty_cycle": 60,
                "waveform": "Square",
            },
            "gantry": {
                "speed": 5000,
                "length_x": 2100,
                "length_y": 2000,
                "offset": 200,
                "cam_height": 1000,
            },
            "camera": {
                "fps": 50,
                "fps_ratio": 6,
                "exposure": 1,
                "gain": "Medium",
            },
        }
        # Update UI
        self._refresh_ui()
    
    def _refresh_ui(self):
        """Refresh all UI widgets with current model values"""
        for widget_key, (widget, var, section, key, widget_type) in self.view.widgets.items():
            value = self.model.get(section, key)
            if widget_type == "checkbox":
                var.set(value)
            else:
                var.set(str(value))


def create_config_window(parent, config_dict=None):
    """Factory function to create and return the config window"""
    model = ConfigModel(config_dict)
    view = ConfigView(parent, model, None)
    controller = ConfigController(model, view)
    view.controller = controller
    
    return view.window, model
