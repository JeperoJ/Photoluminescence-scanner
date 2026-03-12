# Modulated Peak Width Detection

## Overview

When detecting peaks in photoluminescence (PL) signals, you often encounter signals that have **modulation** - high-frequency oscillations on top of a broader peak structure. A simple peak detection algorithm will find many small peaks (the modulation) rather than the overall peak width you're interested in.

This solution provides tools to detect the **envelope** of a modulated signal and determine the overall peak width, even when the signal contains significant high-frequency noise or oscillations.

## Key Concepts

### Problem
You have a signal that looks like this (conceptually):
```
          ╱╲╱╲╱╲╱╲╱╲╱╲╱╲
        ╱╱          ╲╲
      ╱╱              ╲╲
    ╱╱                  ╲╲
```

Where:
- The **outer envelope** (the smooth curve) represents the true peak you want to measure
- The **small oscillations** are the modulation (high-frequency noise)

### Solution
Instead of detecting individual peaks, we:
1. **Extract the envelope** using the Hilbert Transform
2. **Smooth the envelope** (optional) to remove small noise
3. **Detect the main peak** in the envelope
4. **Find peak edges** by looking for where the envelope crosses a threshold

## Files

### `modulated_peak_detector.py`
Main module containing the peak detection algorithms.

**Key Functions:**

#### `detect_modulated_peak_width(signal_data, min_peak_height=None, smoothing_window=None, return_envelope=False)`

Detects the width of a peak composed of many small peaks.

**Parameters:**
- `signal_data`: 1D array of signal values
- `min_peak_height`: Optional height threshold (default: 10% of max envelope)
- `smoothing_window`: Optional window for smoothing (default: signal_length/20)
- `return_envelope`: If True, also return the computed envelope

**Returns:**
```python
{
    'start_idx': 150,           # Starting index of peak
    'end_idx': 350,             # Ending index of peak
    'width': 200,               # Width in samples
    'peak_idx': 250,            # Index of peak center
    'peak_value': 0.95,         # Value at peak center
    'status': 'success'          # 'success' or 'no_clear_peak'
}
```

#### `detect_multiple_modulated_peaks(signal_data, min_prominence=None)`

Detects multiple modulated peaks in a signal.

**Returns:** List of peak dictionaries (same format as above)

### `example_modulated_peak_usage.py`
Example script showing how to use the module with photoluminescence data.

## Usage Examples

### Basic Usage

```python
import numpy as np
from modulated_peak_detector import detect_modulated_peak_width

# Your signal (e.g., a scan profile)
signal = your_scan_data

# Detect peak
peak_info = detect_modulated_peak_width(signal)

print(f"Peak width: {peak_info['width']} samples")
print(f"Peak center: {peak_info['peak_idx']}")
print(f"Peak range: {peak_info['start_idx']} to {peak_info['end_idx']}")
```

### With Visualization

```python
import matplotlib.pyplot as plt
from modulated_peak_detector import detect_modulated_peak_width

# Detect with envelope
peak_info, envelope = detect_modulated_peak_width(signal, return_envelope=True)

# Plot
plt.figure(figsize=(14, 6))
plt.plot(signal, label='Signal', linewidth=1, alpha=0.7)
plt.plot(envelope, label='Envelope', linewidth=2, color='red')
plt.axvline(peak_info['start_idx'], color='green', linestyle='--', label='Peak Start')
plt.axvline(peak_info['end_idx']-1, color='orange', linestyle='--', label='Peak End')
plt.axvline(peak_info['peak_idx'], color='purple', linestyle=':', label='Peak Center')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Multiple Peaks

```python
from modulated_peak_detector import detect_multiple_modulated_peaks

peaks_list = detect_multiple_modulated_peaks(signal)

for i, peak in enumerate(peaks_list):
    print(f"Peak {i}: width={peak['width']}, center={peak['peak_idx']}")
```

### In Your Photoluminescence Analysis

```python
# Extract profile from your scan
scan_profile = np.mean(scan_raw[0], axis=0)  # or any slice/profile

# Detect modulated peak
peak_info, envelope = detect_modulated_peak_width(scan_profile, return_envelope=True)

# Use the detected width for further analysis
if peak_info['status'] == 'success':
    peak_width_mm = peak_info['width'] * pixel_pitch_mm
    print(f"Defect width: {peak_width_mm:.2f} mm")
```

## How It Works

### Step 1: Hilbert Transform (Envelope Extraction)

The **Hilbert Transform** creates an "analytic signal" from your real signal. The magnitude of this analytic signal is the **envelope** - the smooth curve that bounds the oscillations.

**Advantages:**
- Works with any modulation frequency
- Doesn't require knowing the modulation frequency in advance
- Robust to noise
- Preserves the envelope shape

**Disadvantage:**
- Can have edge effects at the start/end of the signal

### Step 2: Smoothing (Optional)

If your envelope is still noisy, you can apply a moving average filter to further smooth it. This is optional but often helpful.

### Step 3: Peak Detection

Using `scipy.signal.find_peaks()`, we detect peaks in the envelope. This finds the main peak without being confused by the small oscillations.

### Step 4: Edge Detection

Once we have the peak, we find where the envelope crosses below a threshold (typically 10% of peak height). This determines the start and end of the peak.

## Parameters and Tuning

### `min_peak_height`
- **What it is:** Minimum height to consider as a peak in the envelope
- **Default:** 10% of maximum envelope value
- **Adjust if:**
  - Peaks are not being detected: increase to 5% or 1%
  - Too many false peaks: increase to 20% or more

### `smoothing_window`
- **What it is:** Size of the moving average filter for smoothing
- **Default:** 1/20 of signal length (must be odd)
- **Adjust if:**
  - Envelope is too noisy: increase (e.g., signal_length/10)
  - Envelope is over-smoothed: decrease (e.g., signal_length/50)

### Threshold for Edge Detection
Currently set to 10% of peak height. To change this, modify the `threshold_ratio` parameter in `_find_peak_edges()`.

## Comparison with Other Methods

### Method 1: Direct Peak Detection
```python
peaks, _ = find_peaks(signal, height=threshold)
```
**Problems:**
- Finds many small peaks (one per oscillation)
- Not suitable for modulated signals
- Unclear which peaks are "real" vs noise

### Method 2: Low-Pass Filtering (Alternative)
```python
from scipy.signal import butter, filtfilt
b, a = butter(3, cutoff_frequency, fs=sampling_rate)
filtered = filtfilt(b, a, signal)
peaks, _ = find_peaks(filtered)
```
**Problems:**
- Requires knowing the modulation frequency
- Can distort the signal if cutoff is not chosen carefully
- Less robust than envelope detection

### Method 3: Envelope Detection (Our Approach) ✓
```python
from modulated_peak_detector import detect_modulated_peak_width
peak_info = detect_modulated_peak_width(signal)
```
**Advantages:**
- No modulation frequency needed
- Extracts true amplitude envelope
- Robust to different modulation patterns
- Handles both symmetric and asymmetric peaks

## Integration with Your Notebook

In your `testing_fps_wrong.ipynb`, you can add:

```python
# At the top of the notebook
from modulated_peak_detector import detect_modulated_peak_width

# In the analysis section
# Assuming you have scan_profile
peak_info, envelope = detect_modulated_peak_width(scan_profile, return_envelope=True)

# Use the results
print(f"Detected peak width: {peak_info['width']} samples")
print(f"Peak center at index: {peak_info['peak_idx']}")

# Replace your manual vlines
plt.plot(scan_profile)
plt.plot(envelope, 'r-', linewidth=2)
plt.axvline(peak_info['start_idx'], 'g--')
plt.axvline(peak_info['end_idx'], 'orange--')
```

## Troubleshooting

### Issue: No peak is detected
**Solution:**
- Lower `min_peak_height` parameter
- Check if signal has meaningful peaks using `plt.plot(signal)`
- Try `detect_multiple_modulated_peaks()` to find all peaks

### Issue: Peak boundaries are too wide/narrow
**Solution:**
- Increase/decrease smoothing_window
- Adjust the threshold_ratio in `_find_peak_edges()`
- Check signal quality/noise level

### Issue: Edge effects at signal boundaries
**Solution:**
- Use a subset of your signal: `peak_info = detect_modulated_peak_width(signal[100:-100])`
- Pad the signal with zeros/constants before detection

## Mathematical Details

### Hilbert Transform
The Hilbert transform $\mathcal{H}[x(t)]$ of a real signal $x(t)$ creates:
$$s_a(t) = x(t) + j \mathcal{H}[x(t)]$$

The envelope is:
$$e(t) = |s_a(t)| = \sqrt{x(t)^2 + \mathcal{H}[x(t)]^2}$$

This is particularly effective for narrowband signals with modulation.

## References

1. Smith, S. W. (1999). "The Scientist and Engineer's Guide to Digital Signal Processing"
2. Hlawatsch, F., & Boudreaux-Bartels, G. F. (1992). "Linear and quadratic time-frequency signal representations"
3. SciPy Documentation: `scipy.signal.hilbert`

## License

Part of the Photoluminescence Scanner project.
