"""
Advanced usage of modulated peak detection for photoluminescence scanning.

This module provides specialized functions for analyzing photoluminescence
and electroluminescence scan data where defects may have modulated signatures.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from modulated_peak_detector import (
    detect_modulated_peak_width,
    detect_multiple_modulated_peaks,
    _find_peak_edges
)


def analyze_scan_line(scan_profile, pixel_pitch=1.0, title="Scan Line Analysis"):
    """
    Analyze a single line from a photoluminescence scan.
    
    Parameters:
    -----------
    scan_profile : array-like
        1D profile extracted from the scan image
    pixel_pitch : float
        Physical size of each pixel (mm). Default: 1.0 (normalized)
    title : str
        Title for the analysis plot
        
    Returns:
    --------
    analysis_dict : dict
        Dictionary with analysis results including:
        - 'width_pixels': Peak width in pixels
        - 'width_physical': Peak width in physical units
        - 'center_pixel': Peak center position in pixels
        - 'contrast': Signal contrast
        - 'status': Detection status
    """
    
    peak_info, envelope = detect_modulated_peak_width(scan_profile, return_envelope=True)
    
    # Calculate contrast
    peak_value = peak_info['peak_value']
    baseline = np.percentile(envelope, 10)
    contrast = (peak_value - baseline) / baseline if baseline > 0 else 0
    
    analysis = {
        'width_pixels': peak_info['width'],
        'width_physical': peak_info['width'] * pixel_pitch,
        'center_pixel': peak_info['peak_idx'],
        'center_physical': peak_info['peak_idx'] * pixel_pitch,
        'start_pixel': peak_info['start_idx'],
        'end_pixel': peak_info['end_idx'],
        'peak_value': peak_info['peak_value'],
        'baseline': baseline,
        'contrast': contrast,
        'status': peak_info.get('status', 'unknown')
    }
    
    # Visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Full signal
    x = np.arange(len(scan_profile)) * pixel_pitch
    axes[0].plot(x, scan_profile, label='Signal', linewidth=1, alpha=0.7)
    axes[0].plot(x, envelope, label='Envelope', linewidth=2.5, color='red')
    axes[0].axhline(baseline, color='gray', linestyle=':', label='Baseline (10%)')
    axes[0].axvline(x[peak_info['start_idx']], color='green', linestyle='--', 
                    linewidth=2, label='Peak Region')
    axes[0].axvline(x[peak_info['end_idx']-1], color='green', linestyle='--', linewidth=2)
    axes[0].fill_between(x[peak_info['start_idx']:peak_info['end_idx']], 
                         axes[0].get_ylim()[0], axes[0].get_ylim()[1],
                         alpha=0.15, color='green')
    axes[0].set_xlabel(f'Position (mm)' if pixel_pitch != 1.0 else 'Position (pixels)')
    axes[0].set_ylabel('Intensity')
    axes[0].set_title(f'{title} - Full Scan')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    # Zoomed region
    margin = max(10, int(peak_info['width'] * 0.2))
    start_idx = max(0, peak_info['start_idx'] - margin)
    end_idx = min(len(scan_profile), peak_info['end_idx'] + margin)
    x_zoom = x[start_idx:end_idx]
    
    axes[1].plot(x_zoom, scan_profile[start_idx:end_idx], label='Signal', linewidth=1)
    axes[1].plot(x_zoom, envelope[start_idx:end_idx], label='Envelope', linewidth=2.5, color='red')
    axes[1].axhline(baseline, color='gray', linestyle=':', label='Baseline')
    axes[1].axvline(x[peak_info['start_idx']], color='green', linestyle='--', linewidth=2)
    axes[1].axvline(x[peak_info['end_idx']-1], color='green', linestyle='--', linewidth=2)
    axes[1].axvline(x[peak_info['peak_idx']], color='orange', linestyle=':', linewidth=2, label='Peak Center')
    
    # Annotate width
    width_annotation = f"Width: {analysis['width_physical']:.2f} mm" if pixel_pitch != 1.0 else f"Width: {analysis['width_pixels']} px"
    axes[1].text(x[peak_info['peak_idx']], axes[1].get_ylim()[1] * 0.95, width_annotation,
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    axes[1].set_xlabel(f'Position (mm)' if pixel_pitch != 1.0 else 'Position (pixels)')
    axes[1].set_ylabel('Intensity')
    axes[1].set_title(f'{title} - Zoomed Peak Region')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    return analysis, fig


def analyze_defect_profile(scan_image, axis=0, pixel_pitch=1.0):
    """
    Analyze a defect profile from a 2D scan image.
    
    Parameters:
    -----------
    scan_image : 2D array
        Image from the scan (height x width)
    axis : int
        Axis along which to extract the profile (0=row average, 1=column average)
    pixel_pitch : float
        Physical pixel size (mm)
        
    Returns:
    --------
    analysis_list : list
        List of analysis dictionaries for each peak found
    profiles : dict
        Dictionary containing the extracted profiles
    """
    
    # Extract profiles
    if axis == 0:
        # Average across rows to get column profile
        profile_main = np.mean(scan_image, axis=0)
        label = 'Column Profile (X-axis)'
    else:
        # Average across columns to get row profile
        profile_main = np.mean(scan_image, axis=1)
        label = 'Row Profile (Y-axis)'
    
    # Detect multiple peaks
    peaks_list = detect_multiple_modulated_peaks(profile_main)
    
    analysis_list = []
    for peak in peaks_list:
        analysis = {
            'width_pixels': peak['width'],
            'width_physical': peak['width'] * pixel_pitch,
            'center_pixel': peak['peak_idx'],
            'center_physical': peak['peak_idx'] * pixel_pitch,
            'peak_value': peak['peak_value'],
            'prominence': peak.get('prominence', 0)
        }
        analysis_list.append(analysis)
    
    # Visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Heat map of original image
    im = axes[0].imshow(scan_image, aspect='auto', cmap='hot', origin='upper')
    axes[0].set_xlabel('Pixel X' if axis == 0 else 'Pixel X')
    axes[0].set_ylabel('Pixel Y' if axis == 1 else 'Pixel Y')
    axes[0].set_title('Scan Image Heatmap')
    plt.colorbar(im, ax=axes[0], label='Intensity')
    
    # Profile with peaks
    x = np.arange(len(profile_main)) * pixel_pitch
    _, envelope = detect_modulated_peak_width(profile_main, return_envelope=True)
    
    axes[1].plot(x, profile_main, label='Signal', linewidth=1, alpha=0.7)
    axes[1].plot(x, envelope, label='Envelope', linewidth=2.5, color='red')
    
    # Mark all peaks
    for i, peak in enumerate(peaks_list):
        axes[1].axvline(x[peak['peak_idx']], color='green', linestyle=':', alpha=0.5)
        axes[1].axvline(x[peak['start_idx']], color='orange', linestyle='--', alpha=0.5)
        axes[1].axvline(x[peak['end_idx']-1], color='orange', linestyle='--', alpha=0.5)
        
        # Annotate
        y_pos = axes[1].get_ylim()[1] * (0.95 - i * 0.05)
        axes[1].text(x[peak['peak_idx']], y_pos, f"W:{peak['width']}", 
                    ha='center', fontsize=8, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    axes[1].set_xlabel(f'Position (mm)' if pixel_pitch != 1.0 else 'Position (pixels)')
    axes[1].set_ylabel('Intensity')
    axes[1].set_title(f'{label} with Detected Peaks')
    axes[1].legend(loc='best')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    profiles = {
        'main': profile_main,
        'envelope': envelope,
    }
    
    return analysis_list, profiles, fig


def extract_defect_metrics(scan_image, pixel_pitch_x=1.0, pixel_pitch_y=1.0):
    """
    Extract comprehensive defect metrics from a scan image.
    
    Parameters:
    -----------
    scan_image : 2D array
        Image data (height x width)
    pixel_pitch_x : float
        Physical size of pixel in X direction (mm)
    pixel_pitch_y : float
        Physical size of pixel in Y direction (mm)
        
    Returns:
    --------
    metrics : dict
        Dictionary containing:
        - defect_width_x: Width in X direction (mm)
        - defect_width_y: Width in Y direction (mm)
        - defect_area: Estimated defect area (mm²)
        - intensity_loss: Percentage intensity loss
        - aspect_ratio: Defect aspect ratio (width_x / width_y)
    """
    
    # Analyze X direction
    analysis_x, _ = analyze_defect_profile(scan_image, axis=0, pixel_pitch=pixel_pitch_x)
    
    # Analyze Y direction
    analysis_y, _ = analyze_defect_profile(scan_image, axis=1, pixel_pitch=pixel_pitch_y)
    
    # Get main peaks
    peak_x = analysis_x[0] if analysis_x else {'width_physical': 0}
    peak_y = analysis_y[0] if analysis_y else {'width_physical': 0}
    
    # Calculate metrics
    width_x = peak_x.get('width_physical', 0)
    width_y = peak_y.get('width_physical', 0)
    
    # Estimate area (ellipse approximation)
    area = np.pi * (width_x / 2) * (width_y / 2) if width_x > 0 and width_y > 0 else 0
    
    # Intensity loss
    avg_intensity = np.mean(scan_image)
    peak_intensity = np.max(scan_image)
    intensity_loss = ((peak_intensity - avg_intensity) / peak_intensity * 100) if peak_intensity > 0 else 0
    
    # Aspect ratio
    aspect_ratio = width_x / width_y if width_y > 0 else 0
    
    metrics = {
        'defect_width_x_mm': width_x,
        'defect_width_y_mm': width_y,
        'defect_area_mm2': area,
        'intensity_loss_percent': intensity_loss,
        'aspect_ratio': aspect_ratio,
        'peak_intensity': peak_intensity,
        'avg_intensity': avg_intensity,
        'analysis_x': analysis_x,
        'analysis_y': analysis_y
    }
    
    print("\n" + "="*60)
    print("DEFECT METRICS SUMMARY")
    print("="*60)
    print(f"Width (X-direction):     {width_x:.3f} mm")
    print(f"Width (Y-direction):     {width_y:.3f} mm")
    print(f"Estimated Area:          {area:.3f} mm²")
    print(f"Aspect Ratio (X/Y):      {aspect_ratio:.3f}")
    print(f"Intensity Loss:          {intensity_loss:.1f}%")
    print(f"Peak Intensity:          {peak_intensity:.1f}")
    print(f"Average Intensity:       {avg_intensity:.1f}")
    print("="*60)
    
    return metrics


def compare_scan_lines(scan_image, num_lines=5, pixel_pitch=1.0):
    """
    Compare multiple horizontal scan lines from an image.
    
    This is useful for verifying that peak detection is consistent
    across the image.
    
    Parameters:
    -----------
    scan_image : 2D array
        Image data
    num_lines : int
        Number of lines to analyze (evenly spaced)
    pixel_pitch : float
        Physical pixel size
        
    Returns:
    --------
    results : list
        List of analysis results for each line
    """
    
    height = scan_image.shape[0]
    indices = np.linspace(0, height - 1, num_lines, dtype=int)
    
    results = []
    
    fig, axes = plt.subplots(num_lines, 1, figsize=(14, 4 * num_lines))
    if num_lines == 1:
        axes = [axes]
    
    for idx, row_idx in enumerate(indices):
        profile = scan_image[row_idx, :]
        analysis, _ = analyze_scan_line(profile, pixel_pitch=pixel_pitch,
                                        title=f"Row {row_idx}")
        results.append(analysis)
        
        # Plot on shared figure
        ax = axes[idx]
        x = np.arange(len(profile)) * pixel_pitch
        _, envelope = detect_modulated_peak_width(profile, return_envelope=True)
        
        ax.plot(x, profile, label='Signal', linewidth=1, alpha=0.7)
        ax.plot(x, envelope, label='Envelope', linewidth=2, color='red')
        ax.axvline(x[analysis['start_pixel']], color='green', linestyle='--', alpha=0.7)
        ax.axvline(x[analysis['end_pixel']-1], color='green', linestyle='--', alpha=0.7)
        ax.set_title(f"Row {row_idx}: Width = {analysis['width_physical']:.2f} mm")
        ax.set_ylabel('Intensity')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        if idx == num_lines - 1:
            ax.set_xlabel('Position (mm)')
    
    plt.tight_layout()
    
    # Summary
    widths = [r['width_physical'] for r in results]
    print(f"\nWidth Statistics across {num_lines} lines:")
    print(f"  Mean:     {np.mean(widths):.3f} mm")
    print(f"  Std Dev:  {np.std(widths):.3f} mm")
    print(f"  Min:      {np.min(widths):.3f} mm")
    print(f"  Max:      {np.max(widths):.3f} mm")
    
    return results


if __name__ == "__main__":
    # Example: Load and analyze a scan
    # from src.utils import ingaas_processing
    # scan_path = "F://Work//LIPI//scans//scan_20260226_152601.raw"
    # scan_raw = ingaas_processing.load_raw_image(scan_path, 640, 512)
    # 
    # # Extract first frame
    # scan_image = scan_raw[0]
    # 
    # # Analyze
    # metrics = extract_defect_metrics(scan_image, pixel_pitch_x=10e-6, pixel_pitch_y=10e-6)
    # 
    # # Compare multiple lines
    # results = compare_scan_lines(scan_image, num_lines=10)
    
    pass
