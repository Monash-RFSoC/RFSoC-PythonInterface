import time

from RFBuilder import *
import numpy as np
import matplotlib.pyplot as plt


board = RFSOC4x2()
rf_builder = RFBuilder(board, "169.254.2.69", 8080)


dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

pb = PulseBlaster()
pb.add_instruction(0, 0, 0, 0, 500, 0, 0, "WAIT", 4)
pb.add_instruction(0, 0, 2**16 - 1, 0, 500, 0, 0, "CONT", 100)
pb.add_instruction(0, 0, 0, 0, 500, 1, 0, "CONT", 500_000_000)
pb.add_instruction(0, 0, 0, 0, 500, 0, 0, "BRANCH", 4)
pb.add_instruction(0, 0, 0, 0, 500, 0, 0, "STOP", 4)

rf_builder.add(pb)
rf_builder.connect(pb, dacs[0]) # Connect PB to DAC_A

logger = DataLogger()
rf_builder.add(logger)
rf_builder.connect(adcs[1], logger)

rf_builder.ttl.reset() # Clears the preset TTL connections AND aliases

trig = ["PB_TRIG", "DIGITIZER_TRIG0", "LED0"]

rf_builder.ttl.connect(["KEY0", "SOFTWARE0"], trig)
rf_builder.ttl.connect("SOFTWARE1", "PB_RSTN")
rf_builder.ttl.connect("SOFTWARE2", "PB_RUN")

rf_builder.ttl.connect("PB_FLAG0", ["SYZYGY_OUT0", "LED1"])

print(rf_builder.ttl.connections)


rf_builder.update()

rf_builder.ttl.update_state("SOFTWARE1", 1)
rf_builder.ttl.update_state("SOFTWARE2", 2)




while True:
    ## Wait for the user to press enter
    input("Press Enter to trigger the pulse sequence...")
    rf_builder.ttl.update_state("SOFTWARE0", 2)
    data, time = logger.read(num_seconds=1000e-9)
    plt.plot(time, data)
    plt.show()


