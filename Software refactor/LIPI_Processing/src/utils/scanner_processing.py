import numpy as np
import scipy
import tifffile
from . import ingaas_processing as ip

def load_scan(source, width, height, crop_rows=None, cal_path=None):
    print("Loading scan")
    if source.endswith('.raw'):
        print("Processing a .raw file")
        images = ip.load_raw_image(source, width, height)
    elif source.endswith('.tiff'):
        print("Processing a .tiff file")
        images = tifffile.imread(source)
    else:
        raise ValueError("Unsupported file format. Please provide a .tiff or .raw file.")
    print(images.shape)
    if cal_path is not None:
        print("Undistorting")
        K, P, DIM = ip.load_calibration(cal_path)
        images = ip.undistort(images, K, P, DIM)
        print(images.shape)
    if crop_rows is not None:
        print("Cropping")
        print(crop_rows)
        images = images[:,crop_rows[0]:crop_rows[1],:]
    return images

def get_phase(x, f, f_s, debug_out=False):
    '''
    Finds the phase of a given frequency in a signal, sampled at some other frequency.

    Args:
        x: The signal as a numpy array
        f: The frequency to find the phase of
        f_s: The frequency at which the signal was sampled
        debug_out: Whether to display some debug info. Matplotlib required.

    Returns:
        phase: The phase of the signal
        f_out: The closest frequency present in the FFT

    '''
    if debug_out:
        import matplotlib.pyplot as plt

    # Where is the modulation frequency in the results?
    fft_frequencies = scipy.fft.fftshift(scipy.fft.rfftfreq(len(x), d=1/f_s))
    f_index = np.argmin(np.abs(f-fft_frequencies))
    f_out = fft_frequencies[f_index]
    if debug_out:
        print(f_index)
        print(f_out)

    # FFT of data
    yf = scipy.fft.fftshift(scipy.fft.rfft(x))
    if debug_out:
        plt.plot(fft_frequencies, yf)
        plt.show()


    # Get phase
    phase = np.angle(yf[f_index])
    if debug_out:
        print(yf[f_index])
        print("Phase:", phase)

    return phase

def get_extrema_window(f,phase,f_s,N):
    '''
    Estimate the extrema points of a discrete signal

    Args:
        f: Frequency of the signal component of interest
        phase: How the signal component is shifted. Should be in the range [-Pi,Pi]
        f_s: Frequency at which the signal is sampled
        start: Index at which to start return from
        end: Index at which to end return at

    Returns:
        peaks: Index of peaks as a numpy array
        valleys: Index of valleys as a numpy array

    '''
    peak_arg =  -phase

    if peak_arg < 0:
        peak_arg += 2*np.pi

    if peak_arg > 2*np.pi:
        peak_arg -= 2*np.pi

    valley_arg = peak_arg + np.pi

    base = np.arange(N)*2*np.pi
    peaks = np.round(f_s*(base+peak_arg)/(2*np.pi*f)).astype(np.int32)
    valleys = np.round(f_s*(base+valley_arg)/(2*np.pi*f)).astype(np.int32)

    #mask = np.all([peaks > start, peaks < end, valleys > start, valleys < end], axis=0)
    mask = np.all([peaks < N, valleys < N], axis=0)
    return peaks[mask], valleys[mask]

def get_extrema_scan(scan, window_length, skip, f_m, fps):
    # Choice to use either steps or window length as hyperparameter. Think window length makes the most sense, due to consistency
    #  between scans. Unsure though.
    # Probably need skip for certain scans.
    signal = np.sum(scan, axis=(1, 2))
    N = len(signal)

    min_steps = np.ceil(N / window_length).astype(np.int32)
    steps = 10 + min_steps
    step_size = (N - skip - window_length) / (steps - 1)

    peaks = np.empty(0, dtype=np.int32)
    valleys = np.empty(0, dtype=np.int32)

    for i in range(steps):
        w_start = round(i * step_size) + skip
        w_end = w_start + window_length
        w_start_next = round((i + 1) * step_size) + skip
        if w_end + 10 > N:
            w_start_next = w_end

        window = signal[w_start:w_end]
        phase = get_phase(window, f_m, fps)
        peaks_i, valleys_i = get_extrema_window(f_m, phase, fps, w_start_next - w_start)
        peaks = np.append(peaks, peaks_i + w_start)
        valleys = np.append(valleys, valleys_i + w_start)

    return peaks, valleys

def SNR50(Img1, Img2, ImgBG, dB=False, profile=True):
    K=np.sqrt(0.5)*((2/np.pi)**(-0.5))
    top = 0.5 * (Img1+Img2-ImgBG)
    bottom = np.abs(Img1-Img2)*K

    snr = top.sum()/bottom.sum()
    if dB:
        snr = 20*np.log10(snr)
    if profile:
        return snr, top.sum(axis=1)/bottom.sum(axis=1)
    else:
        return snr

def SNRAvg(ImgSig, ImgBG, dB=False):
    K=np.sqrt(0.5)*((2/np.pi)**(-0.5))

    set_1 = ImgSig[::2]
    set_2 = ImgSig[1::2]
    N = min(len(set_1), len(set_2))

    top = np.sum(np.mean(ImgSig[:2*N]-ImgBG[:2*N], axis=0))
    bottom = np.sum(np.abs(np.mean(set_1, axis=0)-np.mean(set_2, axis=0))*K)
    snr = top/bottom
    if dB:
        snr = 20*np.log10(snr)
    return snr