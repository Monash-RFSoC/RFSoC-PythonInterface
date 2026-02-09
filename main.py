from RFBuilder import RFBuilder, MemSource, LowPassFilter, WaveType, WaveGenerator, DAC
from RFBuilder.Boards import RFSoC4x2

import numpy as np
import matplotlib.pyplot as plt

import os
import time

BYTE_FUCKERY = 0

# RFSoC requires data sizes to be a multiple of 64 bytes

def main():
    rf_builder = RFBuilder()


    waveData, numBytes = wave_generator(freq=100 * 1e6, wave_type=WaveType.SINE, byte_boundary=4096*2)
    _temp1 = rf_builder.add_block(MemSource(base_address=0, stream_length=(numBytes), data= [i for i in waveData]))
    _temp2 = rf_builder.add_block(DAC())
    rf_builder.add_connection(source= _temp1, sink= _temp2)
    RFSoC4x2.transmit(rf_builder, "192.168.2.69", 8080)
        
        
    # waveData, numBytes, _, _ = frequency_comb_generator(10000000, 1000000000, 100, max_samples=200000)
    # for i in np.arange(9.997, 10.003, 0.0001):
    #     waveData, numBytes = wave_generator(freq=i * 1e6, wave_type=WaveType.SINE, byte_boundary=4096)
    #     _temp1 = rf_builder.add_block(MemSource(base_address=0, stream_length=(numBytes), data= [i for i in waveData]))
    #     _temp2 = rf_builder.add_block(DAC())
    #     rf_builder.add_connection(source= _temp1, sink= _temp2)
    #     RFSoC4x2.transmit(rf_builder, "192.168.2.69", 8080)
    
    #     time.sleep(2)
    
    
    # RFSoC4x2.send_command(data={"request-type": "trigger"}, ip="192.168.2.69", port=8080)
    # plt.plot(waveData[-200:] + waveData[:200])
    # plt.plot(waveData)
    
    # plot vertical lines every 512 samples
    # for i in range(0, len(waveData), 1024):
    #     plt.axvline(x=i, color='r', linestyle='--', alpha=0.5)
        
    # plt.show()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

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
    
    numSamples = int(best_numSamples) - BYTE_FUCKERY
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

def frequency_comb_generator(start_freq: float, stop_freq: float, num_tones: int, 
                           amplitudes: list = None, phases: list = None, 
                           byte_boundary: int = 4096, max_samples: int = 100000) -> tuple:
    """
    Generate a frequency comb with multiple tones aligned to 4096-byte boundaries.
    
    Args:
        start_freq: Starting frequency in Hz
        stop_freq: Ending frequency in Hz 
        num_tones: Number of frequency tones in the comb
        amplitudes: List of amplitudes for each tone (defaults to equal amplitudes)
        phases: List of phases for each tone in radians (defaults to zero)
        byte_boundary: Byte alignment requirement (default 4096)
        max_samples: Maximum number of samples allowed
        
    Returns:
        tuple: (waveform_data_list, num_samples, actual_frequencies, frequency_errors)
    """
    SAMPLE_RATE = 8000000000  # 8 GHz
    BYTES_PER_SAMPLE = 2  # Each sample is 2 bytes (int16)
    tolerance = 10000  # 10kHz tolerance
    
    # Generate frequency list
    if num_tones == 1:
        target_frequencies = [start_freq]
    else:
        target_frequencies = np.linspace(start_freq, stop_freq, num_tones)
    
    # Set default amplitudes and phases if not provided
    if amplitudes is None:
        amplitudes = [1.0 / num_tones] * num_tones  # Equal amplitudes, normalized
    if phases is None:
        phases = [0.0] * num_tones
        
    # Ensure lists are the right length
    if len(amplitudes) != num_tones:
        amplitudes = amplitudes[:num_tones] + [amplitudes[-1]] * (num_tones - len(amplitudes))
    if len(phases) != num_tones:
        phases = phases[:num_tones] + [phases[-1]] * (num_tones - len(phases))
    
    # print(f"Generating frequency comb with {num_tones} tones from {start_freq/1e6:.1f} to {stop_freq/1e6:.1f} MHz")
    
    # Find optimal sample count that works for all frequencies
    best_total_samples = None
    best_total_error = float('inf')
    best_cycles_list = []
    actual_frequencies = []
    
    # Calculate samples per boundary
    samples_per_boundary = byte_boundary // BYTES_PER_SAMPLE
    
    # Try different total sample counts (must be multiples of samples_per_boundary)
    for total_samples in range(samples_per_boundary, max_samples + 1, samples_per_boundary):
        total_error = 0
        cycles_list = []
        freq_list = []
        valid = True
        
        # For each frequency, find the best number of cycles
        for target_freq in target_frequencies:
            best_cycles = 1
            best_freq_error = float('inf')
            
            # Try different cycle counts for this frequency
            max_cycles = int(total_samples * target_freq / SAMPLE_RATE) + 10
            for cycles in range(1, max(2, max_cycles)):
                actual_freq = SAMPLE_RATE * cycles / total_samples
                freq_error = abs(actual_freq - target_freq)
                
                if freq_error < best_freq_error:
                    best_freq_error = freq_error
                    best_cycles = cycles
                    
                # If within tolerance, we can stop searching for this frequency
                if freq_error <= tolerance:
                    break
            
            # Check if this frequency is achievable within tolerance
            if best_freq_error > tolerance * 10:  # Allow some flexibility for multi-tone
                valid = False
                break
                
            cycles_list.append(best_cycles)
            freq_list.append(SAMPLE_RATE * best_cycles / total_samples)
            total_error += best_freq_error
        
        # If all frequencies are valid and this is the best solution so far
        if valid and total_error < best_total_error:
            best_total_error = total_error
            best_total_samples = total_samples
            best_cycles_list = cycles_list.copy()
            actual_frequencies = freq_list.copy()
            
            # If we're within tolerance for all frequencies, we can stop
            if all(abs(actual - target) <= tolerance for actual, target in zip(actual_frequencies, target_frequencies)):
                break
    
    if best_total_samples is None:
        # Fallback to minimum valid samples
        best_total_samples = samples_per_boundary
        best_cycles_list = [1] * num_tones
        actual_frequencies = [SAMPLE_RATE / best_total_samples] * num_tones
    
    numSamples = best_total_samples - BYTE_FUCKERY
    numBytes = numSamples * BYTES_PER_SAMPLE
    
    # Generate time array
    t = np.arange(numSamples) / SAMPLE_RATE
    
    # Generate the frequency comb
    _array = np.zeros(numSamples)
    frequency_errors = []
    
    # print(f"Generating {num_tones} tones with {numSamples} samples ({numBytes} bytes):")
    for i, (target_freq, actual_freq, amplitude, phase) in enumerate(zip(target_frequencies, actual_frequencies, amplitudes, phases)):
        # Add this tone to the combined signal
        tone = amplitude * np.sin(2 * np.pi * actual_freq * t + phase)
        _array += tone
        
        freq_error = abs(actual_freq - target_freq)
        frequency_errors.append(freq_error)
        # print(f"  Tone {i+1}: Target={target_freq/1e6:.3f} MHz, Actual={actual_freq/1e6:.3f} MHz, "
            #   f"Error={freq_error/1e3:.1f} kHz, Amp={amplitude:.3f}, Phase={phase:.2f} rad")
    
    # Scale to use appropriate range for int16
    max_amplitude = np.max(np.abs(_array))
    if max_amplitude > 0:
        scale_factor = 16000 / max_amplitude  # Leave some headroom
        _array = (_array * scale_factor).astype(np.int16)
    else:
        _array = _array.astype(np.int16)
    
    # print(f"Total samples: {numSamples}, Total bytes: {numBytes}, Max amplitude: {np.max(np.abs(_array))}")
    # print(f"Byte boundary alignment: {numBytes} bytes is multiple of {byte_boundary}: {numBytes % byte_boundary == 0}")
    
    return _array.tolist(), numSamples, actual_frequencies, frequency_errors


if __name__ == "__main__":
    main()
    
