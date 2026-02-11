
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster
from RFBuilder import Clock_Config
import numpy as np
import time


board = RFSOC4x2()
rf_builder = RFBuilder(board, "192.168.137.69", 8080)

rf_builder.configure_clock(ref=Clock_Config.Ext_Ref)


dacs = rf_builder.get_dacs()

awg = ArbitraryWaveformGenerator(WaveType.SINE, 500e6)

rf_builder.register_block(awg)
rf_builder.register_connection(awg, dacs[0])


rf_builder.update()
