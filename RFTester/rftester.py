import RFBuilder
import time

from abc import ABC, abstractmethod
import numpy as np
import scipy.signal 
import matplotlib.pyplot as plt

class Base(ABC):
    def __init__(self, rfbuilder: RFBuilder.RFBuilder):
        self.rf_builder = rfbuilder

    @abstractmethod
    def test(self):
        if self.rf_builder is None:
            raise ValueError("RFTester must be initialized with a valid RFBuilder instance.")


    def trim_zeros(self, _data: np.ndarray, _time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ## Trim the leading zeros from the dataset
        zero_threshold = 150

        first_nonzero_index = np.argmax(abs(_data) > zero_threshold) - 1
        pulse_time = _time[first_nonzero_index]

        _duration = pulse_time - _time[0]
        _data = _data[first_nonzero_index:]
        _time = _time[first_nonzero_index:]
    
        return _duration, _data, _time
    
    def trim_pulse(self, _data: np.ndarray, _time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ## Find the cross over between two different frequencies
        zero_threshold = 150

        zero_indices = np.where(abs(_data) <= zero_threshold)[0]
        consecutive_zero_index = zero_indices[np.where(np.diff(zero_indices) == 1)[0] + 1][0]

        pulse_duration = _time[consecutive_zero_index] - _time[0]

        ## Measure the zero crossings of each cycle within the pulse to gets its frequency and amplitude
        pulse_time = _time[:consecutive_zero_index]
        pulse_data = _data[:consecutive_zero_index]

        pulse_amplitude = np.max(pulse_data)
        time_step = np.diff(pulse_time).mean()

        pulse_fft = np.fft.fft(pulse_data)
        freqs = np.fft.fftfreq(len(pulse_time), d=(time_step))
        freqs = freqs[:len(freqs) // 2]
        peak_freq = freqs[np.argmax(np.abs(pulse_fft[:len(pulse_fft) // 2]))]
        pulse_frequency = peak_freq / 1e6

        _data = _data[consecutive_zero_index:]
        _time = _time[consecutive_zero_index:]

        return pulse_duration, pulse_amplitude, pulse_frequency, _data, _time
    

    def __str__(self):
        output = ""
        output += f"[RF Tester]\n"

        output += f"\tLinked RF Builder:\n"
        output += str(self.rf_builder)

        return output

