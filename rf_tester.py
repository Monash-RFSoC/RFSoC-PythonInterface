import time

from RFBuilder import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from RFTester import *

# print("Start")
board = RFSOC4x2()
rf_builder = RFBuilder(board, "169.254.127.84", 8080)

mb = MicroBlaster()
maxAmp = mb.get_max_amp()
mb.add_instruction(0,100*1e6, 0, maxAmp, 100)
mb.add_instruction(0,200*1e6, 0, maxAmp, 100)
mb.add_instruction(0,300*1e6, 0, maxAmp, 100)
mb.add_instruction(0,400*1e6, 0, maxAmp, 100)
mb.add_instruction(0,500*1e6, 0, maxAmp, 100)
# mb.add_instruction(0, 0, "STOP", 100)
mb.end_program(0, 0, 0, maxAmp, 100)


# mb.add_instruction(0, 0, 2**15 - 1, 0, 200, 0, 0, "BRANCH", 500)

rf_tester = MBTester(rf_builder, mb)

_d, _t, _sim_d, _sim_t, _start_time, _worst = rf_tester.test("internal")

print("Done")

## NS Grid
plt.xticks(np.arange(0, max(_t), 1e-9)) # Set x-ticks every 1 ns
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

plt.plot(_t, _d, label="Measured data", alpha=0.7, color="orange", linewidth=2, zorder=1, marker="o", markersize=5, markerfacecolor="red", markeredgecolor="white", markeredgewidth=1, linestyle="--")
plt.plot(_sim_t, _sim_d, label="Simulated data", alpha=0.7, color="blue", linewidth=2, zorder=2)
plt.vlines(_start_time, min(_d), max(_d), colors="r", linestyles="dashed", label="Pulse start time")

# Highlight region around worst sample (_worst) +/- 1 ns
plt.axvspan(_worst - 1e-9, _worst + 1e-9, color='yellow', alpha=0.3, zorder=0)
# Add the highlighted region to the legend
highlight_patch = Patch(facecolor='yellow', alpha=0.3, label='Worst ±1 ns')
handles, labels = plt.gca().get_legend_handles_labels()
handles.append(highlight_patch)
labels.append('Worst ±1 ns')
plt.legend(handles, labels)
plt.vlines(_worst, min(_d), max(_d), colors="purple", linestyles="dashed", label="Worst sample time")

plt.show()



