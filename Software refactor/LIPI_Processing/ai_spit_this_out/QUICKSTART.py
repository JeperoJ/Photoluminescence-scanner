"""
QUICK START GUIDE - Modulated Peak Detection
==============================================

For immediate use in your photoluminescence scanning analysis.
"""

# ============================================================================
# BASIC USAGE - 3 Lines of Code
# ============================================================================

import numpy as np
from modulated_peak_detector import detect_modulated_peak_width

# Your signal
signal = your_scan_profile  # 1D array from your scan

# Detect peak
peak_info = detect_modulated_peak_width(signal)

# Get results
print(f"Peak width: {peak_info['width']} samples")


# ============================================================================
# WITH VISUALIZATION
# ============================================================================

import matplotlib.pyplot as plt
from modulated_peak_detector import detect_modulated_peak_width

signal = your_scan_profile
peak_info, envelope = detect_modulated_peak_width(signal, return_envelope=True)

plt.figure(figsize=(14, 5))
plt.plot(signal, label='Signal', alpha=0.7)
plt.plot(envelope, label='Envelope', linewidth=2, color='red')
plt.axvline(peak_info['start_idx'], 'g--', label='Peak edges')
plt.axvline(peak_info['end_idx']-1, 'g--')
plt.axvline(peak_info['peak_idx'], ':', color='orange', label='Peak center')
plt.xlabel('Sample Index')
plt.ylabel('Intensity')
plt.title(f"Peak Width: {peak_info['width']} samples")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


# ============================================================================
# IN YOUR TESTING NOTEBOOK
# ============================================================================

# At the top of testing_fps_wrong.ipynb, add:
# from modulated_peak_detector import detect_modulated_peak_width

# Then replace your manual peak detection with:
peak_info, envelope = detect_modulated_peak_width(scan_profile, return_envelope=True)

# Use it:
plt.plot(scan_profile)
plt.plot(envelope, 'r-', linewidth=2)
plt.vlines((peak_info['start_idx'], peak_info['end_idx']), 
           scan_profile.min(), scan_profile.max(), 'r')
plt.vlines(peak_info['peak_idx'], scan_profile.min(), scan_profile.max(), 'g')


# ============================================================================
# WITH PHYSICAL UNITS (PHOTOLUMINESCENCE ANALYSIS)
# ============================================================================

from photoluminescence_analysis import analyze_scan_line

# If you know pixel pitch
pixel_pitch_mm = 0.01  # 10 micrometers per pixel

# Analyze your profile
analysis, fig = analyze_scan_line(scan_profile, pixel_pitch=pixel_pitch_mm)

# Get physical measurements
print(f"Peak width: {analysis['width_physical']:.4f} mm")
print(f"Peak center: {analysis['center_physical']:.4f} mm")
print(f"Contrast: {analysis['contrast']:.2f}")


# ============================================================================
# ANALYZING A 2D SCAN IMAGE
# ============================================================================

from photoluminescence_analysis import extract_defect_metrics

# Your scan image (2D array)
scan_image = scan_raw[0]  # First frame from your raw scan

# Extract all defect metrics
metrics = extract_defect_metrics(
    scan_image,
    pixel_pitch_x=10e-6,  # 10 micrometers
    pixel_pitch_y=10e-6
)

# Results
print(f"Defect width (X): {metrics['defect_width_x_mm']:.3f} mm")
print(f"Defect width (Y): {metrics['defect_width_y_mm']:.3f} mm")
print(f"Defect area: {metrics['defect_area_mm2']:.3f} mm²")
print(f"Aspect ratio: {metrics['aspect_ratio']:.2f}")


# ============================================================================
# DETECTING MULTIPLE PEAKS
# ============================================================================

from modulated_peak_detector import detect_multiple_modulated_peaks

signal = your_signal

# Detect all peaks
peaks_list = detect_multiple_modulated_peaks(signal)

# Analyze each
for i, peak in enumerate(peaks_list):
    print(f"Peak {i}:")
    print(f"  Width: {peak['width']} samples")
    print(f"  Center: {peak['peak_idx']}")
    print(f"  Height: {peak['peak_value']:.4f}")
    print(f"  Prominence: {peak['prominence']:.4f}")


# ============================================================================
# PARAMETER TUNING
# ============================================================================

# If peak is not detected:
peak_info = detect_modulated_peak_width(signal, min_peak_height=0.05)  # 5% instead of 10%

# If signal is noisy (needs more smoothing):
peak_info = detect_modulated_peak_width(signal, smoothing_window=51)  # Larger window

# If signal is under-smoothed (needs less smoothing):
peak_info = detect_modulated_peak_width(signal, smoothing_window=11)  # Smaller window


# ============================================================================
# COMPARISON WITH OTHER APPROACHES
# ============================================================================

import numpy as np
from scipy.signal import find_peaks
from modulated_peak_detector import detect_modulated_peak_width

signal = your_signal

# OLD WAY: Direct peak detection (finds all small peaks)
small_peaks, _ = find_peaks(signal)
print(f"Found {len(small_peaks)} small peaks")  # Probably too many!

# NEW WAY: Modulated peak detection (finds overall peak)
peak_info = detect_modulated_peak_width(signal)
print(f"Found 1 main peak with width {peak_info['width']}")  # What you actually want


# ============================================================================
# INTEGRATION WITH CALIBRATION SYSTEM
# ============================================================================

# If you have a calibration with undistorted images:
# from src.utils import ingaas_processing

# undist_path = "PLhigheff_undist.tiff"
# undist_image = ingaas_processing.load_image(undist_path)
# 
# # Extract a defect scan
# defect_profile = undist_image[:, 320]  # Middle column
# 
# # Analyze using calibrated measurements
# pixel_pitch = 10e-6  # From camera spec
# analysis, fig = analyze_scan_line(defect_profile, pixel_pitch=pixel_pitch)
# 
# # Convert to mm
# defect_width_mm = analysis['width_physical']


# ============================================================================
# TROUBLESHOOTING CHECKLIST
# ============================================================================

peak_info = detect_modulated_peak_width(signal)

# Check 1: Is a peak detected?
if peak_info['status'] == 'no_clear_peak':
    print("⚠️  No peak detected. Try:")
    print("  - Check signal quality: plt.plot(signal)")
    print("  - Lower min_peak_height: min_peak_height=0.05")
    print("  - Increase smoothing: smoothing_window=50")

# Check 2: Is the width reasonable?
if peak_info['width'] < 10:
    print("⚠️  Width seems very small. Check if:")
    print("  - Smoothing is too aggressive")
    print("  - Peak threshold is too high")

if peak_info['width'] > len(signal) * 0.9:
    print("⚠️  Width seems too large (almost entire signal).")
    print("  - Check signal: plt.plot(signal)")
    print("  - Increase min_peak_height")

# Check 3: Is the peak centered?
center_pos = peak_info['peak_idx'] / len(signal)
if center_pos < 0.2 or center_pos > 0.8:
    print("⚠️  Peak is at the edge. Consider:")
    print("  - Using a different section of your scan")
    print("  - Padding the signal")


# ============================================================================
# NEXT STEPS
# ============================================================================

# 1. Read the full documentation:
#    MODULATED_PEAK_DETECTION_README.md
#
# 2. Explore advanced features:
#    - detect_multiple_modulated_peaks() for multiple defects
#    - extract_defect_metrics() for 2D images
#    - compare_scan_lines() for consistency checking
#
# 3. Integrate with your analysis:
#    - Use widths for defect classification
#    - Compare before/after cracking
#    - Build statistical models
#
# 4. Customize for your setup:
#    - Adjust pixel_pitch for your camera/optics
#    - Tune smoothing_window for your modulation frequency
#    - Set min_peak_height based on your noise floor
