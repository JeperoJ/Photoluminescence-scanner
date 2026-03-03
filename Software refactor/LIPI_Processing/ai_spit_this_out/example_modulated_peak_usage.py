"""
Example usage of the modulated peak detector with your photoluminescence data.
Add this to your testing_fps_wrong notebook.
"""

import sys
sys.path.insert(0, '.')

import numpy as np
import matplotlib.pyplot as plt
from modulated_peak_detector import detect_modulated_peak_width, detect_multiple_modulated_peaks

# Assuming you have already loaded your data as scan_raw
# and have extracted a scan_profile like in the notebook

def analyze_photoluminescence_signal(scan_profile):
    """
    Analyze a 1D photoluminescence signal to find peak widths despite modulation.
    
    Parameters:
    -----------
    scan_profile : array-like
        1D signal from the scan (e.g., profile along one axis)
        
    Returns:
    --------
    peak_info : dict
        Information about the detected peak
    """
    
    # Method 1: Simple envelope-based detection
    print("="*60)
    print("MODULATED PEAK DETECTION ANALYSIS")
    print("="*60)
    
    peak_info, envelope = detect_modulated_peak_width(scan_profile, return_envelope=True)
    
    print(f"\nDetected Peak:")
    print(f"  Start index: {peak_info['start_idx']}")
    print(f"  End index: {peak_info['end_idx']}")
    print(f"  Width: {peak_info['width']} samples")
    print(f"  Peak center: {peak_info['peak_idx']}")
    print(f"  Peak value: {peak_info['peak_value']:.4f}")
    print(f"  Status: {peak_info.get('status', 'unknown')}")
    
    # Visualize the results
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Plot 1: Signal and envelope with peak boundaries
    axes[0].plot(scan_profile, label='Original Signal', linewidth=1, alpha=0.7)
    axes[0].plot(envelope, label='Envelope (Hilbert)', linewidth=2, color='red')
    axes[0].axvline(peak_info['start_idx'], color='green', linestyle='--', 
                    linewidth=2, label='Peak Start')
    axes[0].axvline(peak_info['end_idx']-1, color='orange', linestyle='--', 
                    linewidth=2, label='Peak End')
    axes[0].axvline(peak_info['peak_idx'], color='purple', linestyle=':', 
                    linewidth=2, label='Peak Center')
    axes[0].fill_between(range(peak_info['start_idx'], peak_info['end_idx']), 
                         axes[0].get_ylim()[0], axes[0].get_ylim()[1], 
                         alpha=0.2, color='green', label='Peak Region')
    axes[0].set_xlabel('Sample Index')
    axes[0].set_ylabel('Amplitude')
    axes[0].set_title('Signal with Detected Peak Envelope')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Zoomed in on the peak region with smoothed envelope
    start = max(0, peak_info['start_idx'] - 10)
    end = min(len(scan_profile), peak_info['end_idx'] + 10)
    x_zoom = range(start, end)
    axes[1].plot(x_zoom, scan_profile[start:end], label='Signal', linewidth=1)
    axes[1].plot(x_zoom, envelope[start:end], label='Envelope', linewidth=2, color='red')
    axes[1].axvline(peak_info['start_idx'], color='green', linestyle='--', linewidth=2)
    axes[1].axvline(peak_info['end_idx']-1, color='orange', linestyle='--', linewidth=2)
    axes[1].axvline(peak_info['peak_idx'], color='purple', linestyle=':', linewidth=2)
    axes[1].set_xlabel('Sample Index')
    axes[1].set_ylabel('Amplitude')
    axes[1].set_title(f'Zoomed Peak Region (Width: {peak_info["width"]} samples)')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return peak_info, envelope


def compare_detection_methods(scan_profile):
    """
    Compare different peak detection methods.
    """
    from scipy.signal import find_peaks
    
    print("\n" + "="*60)
    print("COMPARISON OF DETECTION METHODS")
    print("="*60)
    
    # Method 1: Direct peak detection (finds many small peaks)
    small_peaks, _ = find_peaks(scan_profile, height=np.percentile(scan_profile, 50))
    print(f"\nDirect peak detection found {len(small_peaks)} small peaks")
    if len(small_peaks) > 0:
        print(f"  Peak spacing: {np.mean(np.diff(small_peaks)):.2f} samples")
    
    # Method 2: Modulated peak detection (finds envelope)
    peak_info, envelope = detect_modulated_peak_width(scan_profile, return_envelope=True)
    print(f"\nModulated peak detection found 1 main peak")
    print(f"  Overall width: {peak_info['width']} samples")
    
    # Method 3: Multiple modulated peaks
    peaks_list = detect_multiple_modulated_peaks(scan_profile)
    print(f"\nMultiple modulated peak detection found {len(peaks_list)} peaks")
    for i, p in enumerate(peaks_list):
        print(f"  Peak {i}: width={p['width']}, center={p['peak_idx']}, value={p['peak_value']:.4f}")
    
    return peak_info, peaks_list


# Example with your photoluminescence data:
if __name__ == "__main__":
    # Load your scan data (similar to your notebook)
    # scan_path = "F://Work//LIPI//scans//scan_20260226_152601.raw"
    # scan_raw = ingaas_processing.load_raw_image(scan_path, 640, 512)
    
    # Extract a profile (e.g., a line through the image)
    # scan_profile = np.mean(scan_raw[0], axis=0)  # Example: average across columns
    
    # Then run:
    # peak_info, envelope = analyze_photoluminescence_signal(scan_profile)
    # peak_info_multi, peaks = compare_detection_methods(scan_profile)
    
    pass
