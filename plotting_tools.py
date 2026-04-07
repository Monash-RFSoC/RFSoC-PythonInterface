import matplotlib.pyplot as plt
import numpy as np

def plot_fft(t, d, fs):
    plt.figure()
    plt.subplot(2, 1, 1)

    # plot the last 500 then the first 500 points to show the wraparound clearly
    plt.plot(t, d)
    plt.title(f"Time Domain Signal [fs = {fs} Hz]")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)

    plt.subplot(2, 1, 2)

    fft_mag = np.abs(np.fft.fft(d.astype(np.float64)))
    freqs = np.fft.fftfreq(len(d), 1 / fs)

    fft_mag = np.fft.fftshift(fft_mag)
    freqs = np.fft.fftshift(freqs)

    # Convert magnitude to decibels (add small epsilon to avoid log(0))
    eps = 1e-15
    fft_mag_db = 20 * np.log10(fft_mag + eps)

    plt.plot(freqs, fft_mag_db)

    # Show positive frequencies only and use linear dB scale with ~80 dB dynamic range
    plt.xlim(0, 4e9)
    top_db = np.max(fft_mag_db)
    plt.ylim(top_db - 200, top_db)

    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.grid(True)

    plt.show()