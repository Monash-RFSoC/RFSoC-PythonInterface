from .Source import Source
from RFBuilder.RFBlocks.Base import Port
from enum import Enum

class WaveType(Enum):
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    # PWM = "pwm"
    # NOISE = "noise"


class WaveGenerator(Source):
    def __init__(self, freq: int, wave_type: WaveType, location: str = "rtl") -> None:
        port = Port(direction="output")
        self.freq = freq
        self.wave_type = wave_type

        if location not in ["rtl", "ddr4"]:
            raise ValueError("Location must be either 'rtl' or 'ddr4'.")
        
        if location == "rtl":
            raise NotImplementedError("RTL location not implemented yet.")
        
            
        self.location = location
        super().__init__([port])

    def to_dict(self) -> dict:
        _temp = super().to_dict()

        if self.location == 'ddr4':
            _temp.update({
                "base_address": self.base_address,
                "stream_length": self.stream_length
            })
        _temp['freq'] = self.freq
        _temp['wave_type'] = self.wave_type.value
        return _temp




def wave_generator(freq: int, wave_type: WaveType, byte_boundary: int = 32) -> dict:
    SAMPLE_RATE = 7864320000  # 7.86432 GHz
    
    # Find the best byte boundary that gets within 50kHz of desired frequency
    # We want: actual_freq = SAMPLE_RATE / (numBytes / cycles)
    # So: numBytes = SAMPLE_RATE * cycles / actual_freq
    
    target_freq = freq
    tolerance = 50000  # 50kHz tolerance
    max_samples = 100000  # Maximum 100k samples allowed
    
    # Start with ideal number of samples for a reasonable number of cycles
    # Try different cycle counts to find the best fit within our sample limit
    best_numBytes = None
    best_freq_error = float('inf')
    best_cycles = 1
    
    # Try different numbers of cycles to find the best frequency match
    for cycles in range(1, int(max_samples * freq // int(SAMPLE_RATE) + 100)):
        ideal_samples = SAMPLE_RATE * cycles / target_freq
        
        # Skip if this would exceed our sample limit
        if ideal_samples > max_samples:
            break
            
        # Find closest byte boundaries around this ideal
        lower_bound = int(ideal_samples // byte_boundary) * byte_boundary
        upper_bound = lower_bound + byte_boundary
        
        for candidate_bytes in [lower_bound, upper_bound]:
            if candidate_bytes < byte_boundary or candidate_bytes > max_samples:
                continue
                
            # Calculate actual frequency this would produce
            actual_freq = SAMPLE_RATE * cycles / candidate_bytes
            freq_error = abs(actual_freq - target_freq)
            
            if freq_error < best_freq_error:
                best_freq_error = freq_error
                best_numBytes = candidate_bytes
                best_cycles = cycles
                
                # If we're within tolerance, we can stop searching
                if freq_error <= tolerance:
                    break
        
        # If we found a solution within tolerance, stop searching
        if best_freq_error <= tolerance:
            break
    
    # Ensure we have a valid solution
    if best_numBytes is None:
        best_numBytes = byte_boundary
        best_cycles = 1
    
    numBytes = int(best_numBytes)
    actual_freq = SAMPLE_RATE * best_cycles / numBytes
    # print(f"Target: {target_freq/1e6:.3f} MHz, Actual: {actual_freq/1e6:.3f} MHz, Error: {abs(actual_freq-target_freq)/1e3:.1f} kHz, Samples: {numBytes}, Cycles: {best_cycles}")
    
    _array = np.zeros(numBytes)
    t = np.arange(numBytes) / SAMPLE_RATE
    
    # Use the actual achievable frequency for generation
    gen_freq = actual_freq
    
    if wave_type == WaveType.SINE:
        _array = np.sin(2 * np.pi * gen_freq * t)
    elif wave_type == WaveType.SQUARE:
        _array = np.sign(np.sin(2 * np.pi * gen_freq * t))
    elif wave_type == WaveType.TRIANGLE:
        _array = (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * gen_freq * t))
    elif wave_type == WaveType.SAWTOOTH:
        _array = (2 / np.pi) * np.arctan(np.tan(np.pi * gen_freq * t))
    

    # Scale to use full range of int16 (-32767 to 32767)
    # print(_array.min(), _array.max())

    # _array = _array + 1  # Shift to be all positive for uint16
    _array = ((_array) * 10000).astype(np.int16)

    packet = {
        "request-type": "memory-stream",
        "data": _array.tolist()
    }

    return packet, numBytes