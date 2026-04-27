from RFBuilder import *
import matplotlib.pyplot as plt
import numpy as np
import plotting_tools

board = RFSOC4x2()

rf_builder = RFBuilder(board, "169.254.2.69", 8080)
rf_builder.sinc_filters = 0

dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

mb = MicroBlaster()

rf_builder.add(mb)


AMP = 2**15 - 1
FREQ = np.pi * 100

AMP = AMP / 2

# mb.add_instruction(0, 0, AMP, 0, FREQ, 0, 0, "WAIT", 4)
freqs = range(500, 3000, 2)
if len(freqs) > 2000:
    assert False, "Too many frequencies, reduce the range or increase the step size."

for f in freqs:
    mb.add_instruction(0, f, 0, AMP * 2, 5_000_000, label=f"freq{f}")

mb.branch(0, FREQ, 0, AMP * 2, 500_000,"freq500")
mb.end_program(0, FREQ, 0, AMP * 2, 4)


awg = ArbitraryWaveformGenerator(WaveType.SINE, FREQ * 1e6, amplitude=AMP, tolerance= 1, max_samples=1000000)
rf_builder.add(awg)


rf_builder.ttl.reset()


logger = DataLogger()

rf_builder.add(logger)
rf_builder.connect(mb, dacs[0])

rf_builder.ttl.connect("SOFTWARE0", ["DIGITIZER_TRIG0", "MB_TRIG"])

rf_builder.ttl.connect("SOFTWARE1", "MB_RSTN")

rf_builder.ttl.connect("SOFTWARE2", "MB_RUN")


print(rf_builder.ttl.connections)
rf_builder.ttl.update_state("SOFTWARE1", 0)

rf_builder.update()


rf_builder.ttl.update_state("SOFTWARE2", 0)
rf_builder.ttl.update_state("SOFTWARE1", 1)

rf_builder.ttl.update_state("SOFTWARE2", 1)

# while True:

#     rf_builder.ttl.update_state("SOFTWARE0", 2)

#     # data, t = logger.read(num_seconds=5000e-9)

    # plotting_tools.plot_fft(t, data, 8e9)
    

    # input("PRESS ENTER...")