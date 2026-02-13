
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster, Mixer

board = RFSOC4x2()

rf_builder = RFBuilder(board, "169.254.2.69", 8080)

dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

awg = ArbitraryWaveformGenerator(WaveType.SQUARE, 10e6, amplitude=0.2*16000)
rf_builder.register_block(awg)

mixer = Mixer()
rf_builder.register_block(mixer)

pb = PulseBlaster()
rf_builder.register_block(pb)

## Insert PB instructions here

rf_builder.register_connection(pb, mixer) # Connect ADC_A to Mixer
rf_builder.register_connection(awg, mixer) # Connect AWG to Mixer
rf_builder.register_connection(mixer, dacs[0]) # Connect Mixer to DAC_A

rf_builder.update()
