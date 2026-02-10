
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType
import numpy as np
import time


def main():
    board = RFSOC4x2()

    rf_builder = RFBuilder(board, "169.254.2.69", 8080)
    
    dacs = rf_builder.get_dacs()
    adcs = rf_builder.get_adcs()

    print([dac.name for dac in dacs])
    print([adc.name for adc in adcs])

    awg = ArbitraryWaveformGenerator(WaveType.SINE, 1111e6, tolerance=0.1, max_samples=1e9)

    rf_builder.register_block(awg)

    print(rf_builder)
    print(str(rf_builder.update()))



if __name__ == "__main__":
    main()
    
