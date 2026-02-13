
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster, Mixer, DataLogger
from RFBuilder.networking import send_http_data
import numpy as np
import matplotlib.pyplot as plt

board = RFSOC4x2()

rf_builder = RFBuilder(board, "169.254.2.69", 8080)

dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

logger = DataLogger()
rf_builder.register_block(logger)

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [])
plt.show()

while True:
    wave, time = logger.read()
    line.set_data(time, wave)
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw_idle()
    fig.canvas.flush_events()

# awg = ArbitraryWaveformGenerator(WaveType.SINE, 300e6, amplitude=16000, tolerance=0.01, max_samples=100e9)
# rf_builder.register_block(awg)

# mixer = Mixer()
# rf_builder.register_block(mixer)

# pb = PulseBlaster()
# rf_builder.register_block(pb)
# pb.add_instruction(0, 0, 0, 510, 0b1111, 0, "WAIT", 0)
# pb.add_instruction(0, 0, 0, 510, 0b1111, 0, "CONT", 0)



# rf_builder.register_connection(adcs[0], mixer) # Connect ADC_A to Mixer
# rf_builder.register_connection(awg, mixer) # Connect AWG to Mixer
# rf_builder.register_connection(mixer, dacs[0]) # Connect Mixer to DAC_A

# rf_builder.register_connection(adcs[0], dacs[0]) # Connect ADC_A to DAC_A

# rf_builder.register_connection(awg, dacs[0]) # Connect AWG to DAC_A

# rf_builder.register_connection(pb, dacs[0]) # Connect AWG to DAC_A


# rf_builder.update()
