from ..base import Source
from ..port import Port, PortDirection

import numpy as np

from enum import Enum

class WaveType(Enum):
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"


class ArbitraryWaveformGenerator(Source):
    def __init__(self, wave_type: WaveType, freq: float, amplitude: float = 16000, tolerance: int = 100, max_samples: int = 400e6):
        self.wave_type: WaveType = wave_type
        self.freq: float = freq
        self.amplitude: float = amplitude
        self.tolerance: int = tolerance
        self.max_samples: int = max_samples
        
        super().__init__("ddr4", [Port(PortDirection.OUTPUT, 0)])
    
        self.custom_update = True

    def set_freq(self, freq: float):
        self.freq = freq
        self.dirty = True

    def set_wave_type(self, wave_type: WaveType):
        self.wave_type = wave_type
        self.dirty = True
        
    def generate_waveform(self):
        SAMPLE_RATE = 8000000000
        BYTES_PER_SAMPLE = 2  # Each sample is 2 bytes (int16)
        byte_boundary = 4096 * 2

        # Find the best sample count that aligns to byte boundary and gets within 50kHz of desired frequency
        # We want: actual_freq = SAMPLE_RATE / (numSamples / cycles)
        # So: numSamples = SAMPLE_RATE * cycles / actual_freq

        target_freq = self.freq
        tolerance = self.tolerance  # 100Hz
        max_samples = self.max_samples  # Maximum 300k samples allowed

        # Start with ideal number of samples for a reasonable number of cycles
        # Try different cycle counts to find the best fit within our sample limit
        best_numSamples = None
        best_freq_error = float('inf')
        best_cycles = 1

        # Try different numbers of cycles to find the best frequency match
        for cycles in range(1, int(max_samples * self.freq // int(SAMPLE_RATE) + 100)):
            ideal_samples = SAMPLE_RATE * cycles / target_freq

            # Skip if this would exceed our sample limit
            if ideal_samples > max_samples:
                break

            # Find closest byte boundaries around this ideal (accounting for 2 bytes per sample)
            # We need numSamples * BYTES_PER_SAMPLE to be aligned to byte_boundary
            samples_per_boundary = byte_boundary // BYTES_PER_SAMPLE
            lower_bound = int(ideal_samples // samples_per_boundary) * samples_per_boundary
            upper_bound = lower_bound + samples_per_boundary

            for candidate_samples in [lower_bound, upper_bound]:
                if candidate_samples < samples_per_boundary or candidate_samples > max_samples:
                    continue

                # Calculate actual frequency this would produce
                actual_freq = SAMPLE_RATE * cycles / candidate_samples
                freq_error = abs(actual_freq - target_freq)

                if freq_error < best_freq_error:
                    best_freq_error = freq_error
                    best_numSamples = candidate_samples
                    best_cycles = cycles

                    # If we're within tolerance, we can stop searching
                    if freq_error <= tolerance:
                        break
                    
            # If we found a solution within tolerance, stop searching
            if best_freq_error <= tolerance:
                break
            
        # Ensure we have a valid solution
        if best_numSamples is None:
            samples_per_boundary = byte_boundary // BYTES_PER_SAMPLE
            best_numSamples = samples_per_boundary
            best_cycles = 1

        numSamples = int(best_numSamples)
        numBytes = numSamples * BYTES_PER_SAMPLE  # Convert samples to bytes
        actual_freq = SAMPLE_RATE * best_cycles / numSamples
        # print(f"Target: {target_freq/1e6:.3f} MHz, Actual: {actual_freq/1e6:.3f} MHz, Error: {abs(actual_freq-target_freq)/1e3:.1f} kHz, Samples: {numSamples}, Bytes: {numBytes}, Cycles: {best_cycles}")

        _array = np.zeros(numSamples)
        t = np.arange(numSamples) / SAMPLE_RATE

        # Use the actual achievable frequency for generation
        gen_freq = actual_freq

        if self.wave_type == WaveType.SINE:
            _array = np.sin(2 * np.pi * gen_freq * t)
        elif self.wave_type == WaveType.SQUARE:
            _array = np.sign(np.sin(2 * np.pi * gen_freq * t))
        elif self.wave_type == WaveType.TRIANGLE:
            _array = (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * gen_freq * t))
        elif self.wave_type == WaveType.SAWTOOTH:
            _array = (2 / np.pi) * np.arctan(np.tan(np.pi * gen_freq * t))


        # Scale to use full range of int16 (-32767 to 32767)
        # print(_array.min(), _array.max())

        # _array = _array + 1  # Shift to be all positive for uint16
        _array = ((_array) * self.amplitude).astype(np.int16)

        return _array.tolist(), numBytes
        

    def update(self):
        wave_data, num_bytes = self.generate_waveform()
        
        bytes_array = bytearray()
        for sample in wave_data:
            bytes_array += sample.to_bytes(2, byteorder='little', signed=True)

        return bytes_array, "api/stream"

        
    def to_dict(self):
        wave_data, num_bytes = self.generate_waveform()
        
        self.attributes = {
            "waveform" : [],
            "stream_length" : num_bytes,
            "base_address" : 0x0
        }
        
        return super().to_dict()
    
    def __str__(self):
        output = ""
        output += f"[AWG] Freq = {self.freq} | Wave Type = {self.wave_type.value} | Amplitude = {self.amplitude}\n"
        for port in self.ports:
            output += f"\t\t{str(port)}\n"

        
        return output
    
    
    
    