
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster
from RFBuilder import Clock_Config
import numpy as np
import time


board = RFSOC4x2()
rf_builder = RFBuilder(board, "192.168.137.69", 8080)

<<<<<<< HEAD
rf_builder.configure_clock(ref=Clock_Config.Ext_Ref)
=======
    rf_builder = RFBuilder(board, "192.168.137.69", 8080)
    
    dacs = rf_builder.get_dacs()
    adcs = rf_builder.get_adcs()

    print([dac.name for dac in dacs])
    print([adc.name for adc in adcs])

    #awg = ArbitraryWaveformGenerator(WaveType.SINE, 1111e6, tolerance=0.1, max_samples=1e9)

    #rf_builder.register_block(awg)
    
    pb = PulseBlaster()    
    rf_builder.register_block(pb)
    pb.add_instruction(0,0,0,10,0b1100,0,"CONT",400*10**6)
    pb.add_instruction(0,0,0,20,0b0100,0,"CONT",400*10**6)
    pb.add_instruction(0,0,0,0,0b1000,0,"STOP",400*10**6)
    pb.print_program()

    print(rf_builder)
    print(str(rf_builder.update()))
>>>>>>> 1981298e3f75fef385aff7ead3477fcf3a26c962


dacs = rf_builder.get_dacs()

awg = ArbitraryWaveformGenerator(WaveType.SINE, 500e6)

rf_builder.register_block(awg)
rf_builder.register_connection(awg, dacs[0])


rf_builder.update()
