"""
Detects the width of a peak that consists of many small peaks (modulated signal).

This module provides functionality to find the envelope of a modulated signal and
determine the overall peak width, even when the signal is composed of many small
oscillations.
"""

import numpy as np
from scipy import signal
from scipy.signal import find_peaks


def detect_modulated_peak_width(signal_data, min_peak_height=None, 
                                smoothing_window=None, return_envelope=False):
    """
    Detect the width of a peak composed of many small peaks (modulated signal).
    
    This function is useful when your signal contains high-frequency modulation
    on top of a broader peak structure. It finds the envelope of the signal and
    detects the overall peak width.
    
    Parameters:
    -----------
    signal_data : array-like
        The input signal (1D array)
    min_peak_height : float, optional
        Minimum height threshold for peak detection on the envelope.
        If None, uses 10% of the envelope's maximum.
    smoothing_window : int, optional
        Window size for smoothing the envelope. 
        If None, uses 1/20 of the signal length (rounded to odd number).
    return_envelope : bool, default False
        If True, also returns the computed envelope
        
    Returns:
    --------
    peak_info : dict
        Dictionary containing:
        - 'start_idx': Starting index of the main peak
        - 'end_idx': Ending index of the main peak
        - 'width': Width in samples (end_idx - start_idx)
        - 'peak_idx': Index of the peak center
        - 'peak_value': Value at the peak
        
    envelope : array, optional (if return_envelope=True)
        The computed envelope of the signal
        
    Examples:
    ---------
    >>> import numpy as np
    >>> t = np.linspace(0, 10, 1000)
    >>> # Signal with modulated peak
    >>> signal = np.exp(-(t-5)**2 / 2) * (1 + 0.5 * np.sin(20 * np.pi * t))
    >>> peak_info = detect_modulated_peak_width(signal)
    >>> print(f"Peak width: {peak_info['width']} samples")
    """
    
    signal_array = np.asarray(signal_data, dtype=float)
    
    # Compute the envelope using Hilbert transform
    # This is a robust method for finding the envelope of oscillating signals
    envelope = _compute_envelope_hilbert(signal_array)
    
    # Apply smoothing if requested
    if smoothing_window is None:
        smoothing_window = max(3, int(len(signal_array) / 20))
        if smoothing_window % 2 == 0:
            smoothing_window += 1
    
    if smoothing_window > 1:
        envelope = _smooth_signal(envelope, smoothing_window)
    
    # Detect peaks on the envelope
    if min_peak_height is None:
        min_peak_height = np.max(envelope) * 0.1
    
    peaks, properties = find_peaks(envelope, height=min_peak_height)
    
    if len(peaks) == 0:
        # No peaks found, return basic info
        peak_info = {
            'start_idx': 0,
            'end_idx': len(signal_array),
            'width': len(signal_array),
            'peak_idx': np.argmax(envelope),
            'peak_value': np.max(envelope),
            'status': 'no_clear_peak'
        }
    else:
        # Find the main peak (highest one)
        main_peak_idx = peaks[np.argmax(properties['peak_heights'])]
        
        # Find the start and end of this peak using the envelope
        start_idx, end_idx = _find_peak_edges(envelope, main_peak_idx)
        
        peak_info = {
            'start_idx': start_idx,
            'end_idx': end_idx,
            'width': end_idx - start_idx,
            'peak_idx': main_peak_idx,
            'peak_value': envelope[main_peak_idx],
            'status': 'success'
        }
    
    if return_envelope:
        return peak_info, envelope
    else:
        return peak_info


def _compute_envelope_hilbert(signal_data):
    """
    Compute the envelope of a signal using the Hilbert transform.
    
    The Hilbert transform creates an analytic signal, and the envelope is the
    magnitude of this analytic signal.
    """
    analytic_signal = signal.hilbert(signal_data)
    envelope = np.abs(analytic_signal)
    return envelope


def _compute_envelope_peak_detect(signal_data, prominence_ratio=0.5):
    """
    Alternative envelope computation by finding local maxima and minima.
    Less robust than Hilbert transform for high-frequency modulation.
    """
    # Find local maxima
    peaks, _ = find_peaks(signal_data)
    # Find local minima (by inverting the signal)
    troughs, _ = find_peaks(-signal_data)
    
    # Combine and sort indices
    extrema = np.sort(np.concatenate([peaks, troughs]))
    
    # Interpolate between peaks to create envelope
    if len(peaks) < 2:
        return np.abs(signal_data)
    
    from scipy.interpolate import interp1d
    envelope_from_peaks = interp1d(peaks, signal_data[peaks], kind='cubic', 
                                   fill_value='extrapolate')(np.arange(len(signal_data)))
    return np.abs(envelope_from_peaks)


def _smooth_signal(signal_data, window_size):
    """
    Smooth a signal using a moving average filter.
    
    Parameters:
    -----------
    signal_data : array-like
        Input signal
    window_size : int
        Window size for the moving average (should be odd)
        
    Returns:
    --------
    smoothed : array
        Smoothed signal
    """
    window = np.ones(window_size) / window_size
    smoothed = np.convolve(signal_data, window, mode='same')
    return smoothed


def _find_peak_edges(envelope, peak_idx, threshold_ratio=0.1):
    """
    Find the start and end indices of a peak in the envelope.
    
    Parameters:
    -----------
    envelope : array
        The envelope signal
    peak_idx : int
        Index of the peak
    threshold_ratio : float
        Fraction of peak height to use as threshold (default 0.1 = 10%)
        
    Returns:
    --------
    start_idx, end_idx : tuple of int
        Indices where the peak starts and ends
    """
    peak_height = envelope[peak_idx]
    threshold = peak_height * threshold_ratio
    
    # Find where the signal crosses below the threshold going left from peak
    start_idx = peak_idx
    for i in range(peak_idx - 1, -1, -1):
        if envelope[i] < threshold:
            start_idx = i + 1
            break
    else:
        start_idx = 0
    
    # Find where the signal crosses below the threshold going right from peak
    end_idx = peak_idx
    for i in range(peak_idx + 1, len(envelope)):
        if envelope[i] < threshold:
            end_idx = i - 1
            break
    else:
        end_idx = len(envelope) - 1
    
    return start_idx, end_idx + 1


def detect_multiple_modulated_peaks(signal_data, min_prominence=None):
    """
    Detect multiple modulated peaks in a signal.
    
    Parameters:
    -----------
    signal_data : array-like
        The input signal
    min_prominence : float, optional
        Minimum prominence for peak detection on the envelope.
        If None, uses automatic detection.
        
    Returns:
    --------
    peaks_list : list of dict
        List of dictionaries, each containing peak information
    """
    signal_array = np.asarray(signal_data, dtype=float)
    envelope, _ = detect_modulated_peak_width(signal_array, return_envelope=True)
    
    if min_prominence is None:
        min_prominence = (np.max(envelope) - np.mean(envelope)) * 0.1
    
    peaks, properties = find_peaks(envelope, prominence=min_prominence)
    
    peaks_list = []
    for peak_idx in peaks:
        start_idx, end_idx = _find_peak_edges(envelope, peak_idx)
        peaks_list.append({
            'start_idx': start_idx,
            'end_idx': end_idx,
            'width': end_idx - start_idx,
            'peak_idx': peak_idx,
            'peak_value': envelope[peak_idx],
            'prominence': properties['prominences'][list(peaks).index(peak_idx)]
        })
    
    return peaks_list


if __name__ == "__main__":
    # Example usage
    import matplotlib.pyplot as plt
    
    # Create a test signal with modulated peak
    t = np.linspace(0, 10, 1000)
    # Gaussian envelope with sinusoidal modulation
    signal = np.exp(-(t - 5) ** 2 / 2) * (1 + 0.5 * np.sin(20 * np.pi * t))
    
    # Detect the peak width
    peak_info, envelope = detect_modulated_peak_width(signal, return_envelope=True)
    
    # Plot results
    plt.figure(figsize=(12, 6))
    plt.plot(t, signal, label='Signal', linewidth=1)
    plt.plot(t, envelope, label='Envelope', linewidth=2, color='red')
    plt.axvline(t[peak_info['start_idx']], color='green', linestyle='--', label='Peak edges')
    plt.axvline(t[peak_info['end_idx']-1], color='green', linestyle='--')
    plt.axvline(t[peak_info['peak_idx']], color='orange', linestyle=':', label='Peak center')
    
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.title(f"Modulated Peak Detection (Width: {peak_info['width']} samples)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print(f"Peak width: {peak_info['width']} samples")
    print(f"Peak center: {peak_info['peak_idx']}")
    print(f"Peak value: {peak_info['peak_value']:.4f}")
