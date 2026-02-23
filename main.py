
from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster, Mixer, DataLogger
from RFBuilder.networking import send_http_data
import numpy as np
import matplotlib.pyplot as plt

board = RFSOC4x2()

rf_builder = RFBuilder(board, "192.168.137.69", 8080)

dacs = rf_builder.get_dacs()
adcs = rf_builder.get_adcs()


pb = PulseBlaster()
rf_builder.register_block(pb)
#rf_builder.register_connection(pb,dacs[0])
pb.add_instruction(0, 0, 0, 510, 0b1111, 0, "WAIT", 0)
pb.add_instruction(0, 0, 0, 510, 0b1001, 0, "CONT", 0)
pb.add_instruction(0,0,0,0,0,0,"STOP",0)
pb.print_program()
pb.run(0)
rf_builder.update()
pb.get_pins()

print("\n\n----------USER INTERFACE----------\n\n")
while True:
    print("Please input an integer coresponding to one of the following options")
    userInput = input("0. Exit program\n1. Pulse run\n2. Pulse trigger\n3. Set run = 1\n4. Set run = 0\n")
    if(userInput == "0"):
        print("Exiting program. Have a nice day :)")
        break
    elif(userInput == "1"):
        print("Pulsing run")
        pb.pulse_pin("run")
    elif(userInput == "2"):
        print("Pulsing trigger")
        pb.pulse_pin("trigger")
    elif(userInput == "3"):
        print("Run set to 1")
        pb.set_pin("run",1)
    elif(userInput == "4"):
        print("Run set to 0")
        pb.set_pin("run",0)
    else:
        print(f"Input of value {userInput} is not an avalible option. Please try again\n")