
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster, Mixer

board = RFSOC4x2()

rf_builder = RFBuilder(board, "169.254.2.69", 8080)

dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

# awg = ArbitraryWaveformGenerator(WaveType.SINE, 500e6, amplitude=0.1*16000, tolerance=0.01, max_samples=1e9)
# rf_builder.register_block(awg)

mixer = Mixer()
rf_builder.register_block(mixer)

pb = PulseBlaster()
rf_builder.register_block(pb)
pb.add_instruction(0, 0, 0, 500, 0, 0, "WAIT", 0)
pb.add_instruction(0, 0, 0, 500, 0, 0, "CONT", 0)



# rf_builder.register_connection(adcs[0], mixer) # Connect ADC_A to Mixer
# rf_builder.register_connection(awg, mixer) # Connect AWG to Mixer
# rf_builder.register_connection(mixer, dacs[0]) # Connect Mixer to DAC_A

# rf_builder.register_connection(adcs[0], dacs[0]) # Connect ADC_A to DAC_A

# rf_builder.register_connection(awg, dacs[0]) # Connect AWG to DAC_A

rf_builder.register_connection(pb, dacs[0]) # Connect AWG to DAC_A


rf_builder.update()
