import time

from RFBuilder import *
import numpy as np
import matplotlib.pyplot as plt

# print("Start")
board = RFSOC4x2()
rf_builder = RFBuilder(board, "169.254.127.84", 8080)

# print("Made RF builder")
dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()

# print("Made DACs and ADCs")
pb = PulseBlaster()
# print("Made pulse blaster")
pb.add_instruction(0, 0, 2**16-1, 0, 3500, 0, 0, "WAIT", 100) #0b1011011111111111
pb.add_instruction(0, 0, 2**16-1, 0, 3500, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 1723, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 1723, 0, 0, "CONT", 10000)
pb.print_program()
# pb.add_instruction(0, 0, (2**16)-1, 0, 250, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 250, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 500, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 500, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 1000, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 1000, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 1500, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 1500, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 2000, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 2000, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 2500, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 2500, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 3000, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 3000, 0, 0, "CONT", 10000)
# pb.add_instruction(0, 0, (2**16)-1, 0, 3500, 0, 0, "WAIT", 100)
# pb.add_instruction(0, 0, (2**16)-1, 0, 3500, 0, 0, "CONT", 10000)


#pb.add_instruction(0, 0, 0, 0, 500, 0, 0, "BRANCH", 4)
pb.add_instruction(0, 1, (2**16)-1, 0, 0, 0, 0b111111111111, "STOP", 4)
# print("Made PB instructions")

rf_builder.register_block(pb)
rf_builder.register_connection(pb, dacs[0]) # Connect PB to DAC_A

rf_builder.ttl.reset() # Clears the preset TTL connections AND aliases

trig = ["PB_TRIG", "LED0"]

rf_builder.ttl.connect(["KEY0", "SOFTWARE0"], trig)
rf_builder.ttl.connect("SOFTWARE1", "PB_RSTN")
rf_builder.ttl.connect("SOFTWARE2", "PB_RUN")

rf_builder.ttl.connect("PB_FLAG0", "SYZYGY_OUT0")
rf_builder.ttl.connect("PB_FLAG1","LED1")

# print("TTL setup done")
print(rf_builder.ttl.connections)

print("Running update PB")
rf_builder.update()
#print("Passed update")
print("Update PB passed")
rf_builder.ttl.update_state("SOFTWARE1", 1)
rf_builder.ttl.update_state("SOFTWARE2", 2)
print("Run trigger passed")

while True:
    try:
        input("Press enter to step to next Frequency...\n")
        rf_builder.ttl.update_state("SOFTWARE0",2)
    except KeyboardInterrupt:
        print("Exiting...\n")
        break
        

