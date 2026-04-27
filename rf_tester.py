import time

from RFBuilder import *
import numpy as np
import matplotlib.pyplot as plt

from RFTester import *

# print("Start")
board = RFSOC4x2()
rf_builder = RFBuilder(board, "169.254.2.69", 8080)

mb = MicroBlaster()
maxAmp = mb.get_max_amp()
mb.add_instruction(0,100, 0, maxAmp, 100)
mb.add_instruction(0,200, 0, maxAmp, 100)
mb.add_instruction(0,300, 0, maxAmp, 100)
mb.add_instruction(0,400, 0, maxAmp, 100)
mb.add_instruction(0,500, 0, maxAmp, 100)
mb.add_instruction(0, 0, "STOP", 100)

# mb.add_instruction(0, 0, 2**15 - 1, 0, 200, 0, 0, "BRANCH", 500)

rf_tester = MBTester(rf_builder, mb)

_d, _t, _sim_d, _sim_t, _start_time = rf_tester.test("internal")



print("Done")

plt.plot(_t, _d, label="Measured data", alpha=0.7, color="orange", linewidth=2, zorder=1, marker="o", markersize=5, markerfacecolor="red", markeredgecolor="white", markeredgewidth=1, linestyle="--")
plt.plot(_sim_t, _sim_d, label="Simulated data", alpha=0.7, color="blue", linewidth=2, zorder=2)
plt.vlines(_start_time, min(_d), max(_d), colors="r", linestyles="dashed", label="Pulse start time")
plt.show()



