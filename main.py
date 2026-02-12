
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster
import numpy as np
import time


def main():
    board = RFSOC4x2()

    rf_builder = RFBuilder(board, "192.168.137.69", 8080)
    
    dacs = rf_builder.get_dacs()
    adcs = rf_builder.get_adcs()

    print([dac.name for dac in dacs])
    print([adc.name for adc in adcs])

    #awg = ArbitraryWaveformGenerator(WaveType.SINE, 10e6, tolerance=0.1, max_samples=1e9, amplitude=2**15-1)

    #rf_builder.register_block(awg)
    
    pb = PulseBlaster()    
    rf_builder.register_block(pb)
    pb.add_instruction(0,0,0,10,0b1111,0,"CONT",50*10**6)
    pb.add_instruction(0,0,0,20,0b1111,0,"CONT",50*10**6)
    pb.add_instruction(0,0,0,0,0b1111,0,"STOP",50*10**6)
    pb.print_program()

    rf_builder.set_pin(pb.trigger,1) #IO to set, value to set it to
    rf_builder.pulse_pin(pb.run,10) #IO to set, Microseconds to hold high

    print(rf_builder)
    print(str(rf_builder.update()))



if __name__ == "__main__":
    main()
    
