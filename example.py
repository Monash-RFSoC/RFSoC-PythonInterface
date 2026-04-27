from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, MicroBlaster, Mixer

board = RFSOC4x2()

rf_builder = RFBuilder(board, "169.254.2.69", 8080)

dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

awg = ArbitraryWaveformGenerator(WaveType.SINE, 500e6)
rf_builder.register_block(awg)


rf_builder.register_connection(awg, dacs[0]) 


rf_builder.update()
