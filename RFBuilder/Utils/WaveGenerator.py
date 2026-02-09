# from RFBuilder.RFBlocks.Sources.WaveGenerator import WaveType

class WaveType:
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"

import numpy as np



def wave_generator(freq: int, wave_type: WaveType, byte_boundary: int = 32) -> dict:
    SAMPLE_RATE = 8000000000  # 7.86432 GHz
    BYTES_PER_SAMPLE = 2  # Each sample is 2 bytes (int16)
    
    # Find the best sample count that aligns to byte boundary and gets within 50kHz of desired frequency
    # We want: actual_freq = SAMPLE_RATE / (numSamples / cycles)
    # So: numSamples = SAMPLE_RATE * cycles / actual_freq
    
    target_freq = freq
    tolerance = 100  # 50kHz tolerance
    max_samples = 20000  # Maximum 100k samples allowed
    
    # Start with ideal number of samples for a reasonable number of cycles
    # Try different cycle counts to find the best fit within our sample limit
    best_numSamples = None
    best_freq_error = float('inf')
    best_cycles = 1
    
    # Try different numbers of cycles to find the best frequency match
    for cycles in range(1, int(max_samples * freq // int(SAMPLE_RATE) + 100)):
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
    _array = ((_array) * 16000).astype(np.int16)

    return _array.tolist(), numBytes