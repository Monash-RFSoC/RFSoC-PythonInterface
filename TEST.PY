from RFBuilder import *


import time

from RFBuilder import *
import numpy as np
import matplotlib.pyplot as plt

# print("Start")
board = RFSOC4x2()
rf_builder = RFBuilder(board, "169.254.2.69", 8080)

# print("Made RF builder")
dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

awg = ArbitraryWaveformGenerator(WaveType.SINE, 1000e6)
rf_builder.add(awg)
rf_builder.connect(awg, dacs[0]) # Connect AWG to DAC_A

logger = DataLogger()
rf_builder.add(logger)
rf_builder.connect(adcs[1], logger)

rf_builder.ttl.connect("SOFTWARE3", ["DIGITIZER_TRIG0", "LED0"])
rf_builder.ttl.connect("SOFTWARE2", ["PB_RSTN"])

rf_builder.ttl.update_state("SOFTWARE1", 0)
rf_builder.update()

print(rf_builder.ttl.connections)
rf_builder.ttl.update_state("SOFTWARE3", 1)
time.sleep(0.5)
rf_builder.ttl.update_state("SOFTWARE3", 0)

data, t = logger.read(num_seconds=100e-9)

plt.plot(t, data)
plt.show()

