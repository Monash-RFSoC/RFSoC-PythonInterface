import RFBuilder
import time

from abc import ABC
import numpy as np
import scipy.signal 
import matplotlib.pyplot as plt

class RFTester(ABC):
    def __init__(self, rfbuilder: RFBuilder.RFBuilder):
        self.rf_builder = rfbuilder

    def test_internal(self, pb: RFBuilder.PulseBlaster):
        if self.rf_builder is None:
            raise ValueError("RFTester must be initialized with a valid RFBuilder instance.")
        
        print("Running RF tester...")

        # if self.rf_builder.is_dirty():
        #     print("Warning: RFBuilder has unsaved changes. Please call rf_builder.update() before testing for accurate results.")

        pb.prepend_instruction(0, 0, 0, 0, 500, 0, 0, "CONT", 100)
        pb.prepend_instruction(0, 0, 2**15-1, 0, 500, 0, 0, "CONT", 82)
        pb.prepend_instruction(0, 0, 0, 0, 500, 0, 0, "WAIT", 4)

        self.rf_builder.add(pb)

        logger = RFBuilder.DataLogger()
        self.rf_builder.add(logger)

        dacs = self.rf_builder.get_dacs()
        self.rf_builder.connect(pb, logger)

        self.rf_builder.ttl.reset()

        self.rf_builder.ttl.connect("SOFTWARE0", ["DIGITIZER_TRIG0", "PB_TRIG", "SYZYGY_OUT0"])
        self.rf_builder.ttl.connect("SOFTWARE1", "PB_RSTN")
        self.rf_builder.ttl.connect("SOFTWARE2", "PB_RUN")

        self.rf_builder.ttl.update_state("SOFTWARE1", 0)
        self.rf_builder.ttl.update_state("SOFTWARE1", 1)
        self.rf_builder.ttl.update_state("SOFTWARE2", 0)
        self.rf_builder.ttl.update_state("SOFTWARE0", 0)

        self.rf_builder.update()

        ## Pulse blaster has had a small 'wait' instruction prepended to it, so the users program should not be running yet.
        # will only test ~10 micro-seconds worth of pulses.
        
        ## Run the pulse blaster, it should stop at the test harness WAIT command
        self.rf_builder.ttl.update_state("SOFTWARE2", 1)

        ## Trigger the blaster and digitizer capture.
        self.rf_builder.ttl.update_state("SOFTWARE0", 2)

        ## Read 10.5 micro-seconds. 10 micro-seconds for the test, and 0.5 at the start for delays and other shenanigans.
        test_data, test_time = logger.read(num_seconds=1.5e-6)
        og_data = test_data.copy()
        og_time = test_time.copy()

        print("Data logger read complete. Data:")

        ## Read statistics
        ## Number of "0" samples at the start, measures the delay between triggering and output
        pulse_time, test_data, test_time = self.trim_zeros(test_data, test_time)
        print(f"\tTrimmed start delay of {pulse_time * 1e9:.2f} ns")

        ## Find the end of the pulse by looking for two consecutive "0" samples, measures the pulse duration
        duration, amplitude, frequency, test_data, test_time = self.trim_pulse(test_data, test_time)

        print(f"\n\tTest start pulse detected!!!")
        print(f"\tTrigger Pulse duration was {duration * 1e9:.2f} ns")
        print(f"\tTrigger Pulse frequency was {frequency:.2f} MHz\n")

        pulse_time, test_data, test_time = self.trim_zeros(test_data, test_time)
        print(f"\tTrimmed user start delay of {pulse_time * 1e9:.2f} ns")


        ## At this point, test_data and test_time only contain the information from the start of the user program.
        pulseBlasterOutput = pb.generate_waveform()

        print("Pulse blaster output:")
        print(pulseBlasterOutput)

        return og_data, og_time

    def find_pulses(self, spectrogram: tuple[np.ndarray, np.ndarray, np.ndarray]) -> list[tuple[float, float, float]]:
        """Identify concatenated tones by tracking the dominant frequency per time frame.

        Returns a list of (start_time_s, frequency_hz, duration_s).
        """
        frequencies, times, Sxx = spectrogram
        if Sxx.size == 0 or len(times) == 0:
            return []

        # dominant frequency index per time column
        peak_idx = np.argmax(Sxx, axis=0)
        peak_freqs = frequencies[peak_idx]

        # median filter to reduce jitter (small kernel)
        try:
            peak_freqs_smooth = scipy.signal.medfilt(peak_freqs, kernel_size=3)
        except Exception:
            peak_freqs_smooth = peak_freqs

        # set tolerance to half a frequency bin to detect real jumps
        if len(frequencies) > 1:
            freq_bin = abs(frequencies[1] - frequencies[0])
        else:
            freq_bin = 1.0
        tol = freq_bin / 2.0

        pulses: list[tuple[float, float, float]] = []
        start_idx = 0
        cur_freq = peak_freqs_smooth[0]

        for i in range(1, len(times)):
            if abs(peak_freqs_smooth[i] - cur_freq) > tol:
                start_time = times[start_idx]
                end_time = times[i - 1]
                duration = max(0.0, end_time - start_time)
                mean_freq = float(np.mean(peak_freqs_smooth[start_idx:i]))
                pulses.append((start_time, mean_freq, duration))
                start_idx = i
                cur_freq = peak_freqs_smooth[i]

        # add final segment
        start_time = times[start_idx]
        end_time = times[-1]
        duration = max(0.0, end_time - start_time)
        mean_freq = float(np.mean(peak_freqs_smooth[start_idx:]))
        pulses.append((start_time, mean_freq, duration))

        return pulses


    def trim_zeros(self, _data: np.ndarray, _time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ## Trim the leading zeros from the dataset
        first_nonzero_index = np.argmax(_data != 0)
        pulse_time = _time[first_nonzero_index]

        _duration = pulse_time - _time[0]
        _data = _data[first_nonzero_index - 1:]
        _time = _time[first_nonzero_index - 1:]
    
        return _duration, _data, _time
    
    def trim_pulse(self, _data: np.ndarray, _time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ## Find the cross over between two different frequencies

        zero_indices = np.where(_data == 0)[0]
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
    def test_feedback(self, pb):
        pass
    

    def __str__(self):
        output = ""
        output += f"[RF Tester]\n"

        output += f"\tLinked RF Builder:\n"
        output += str(self.rf_builder)

        return output

