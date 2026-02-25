from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, PulseBlaster, Mixer, DataLogger
from RFBuilder.networking import send_http_data
import numpy as np
import matplotlib.pyplot as plt

board = RFSOC4x2()

rf_builder = RFBuilder(board, "192.168.137.69", 8080)

dacs = rf_builder.get_dacs()
pb = PulseBlaster()
rf_builder.register_block(pb)
pb.set_pin("run",0)
pb.set_pin("trigger",0)
rf_builder.register_connection(pb, dacs[0])

for i in range(10):
    pb.add_instruction(0, 0, 0, 0, 0b001100000000, 0, "WAIT", 2*(i+1)) #0
    pb.add_instruction(0, 0, 0, 0, 0b0000000000, 100, "LOOP", 2*(i+1)) #1
    pb.add_instruction(0, 0, 0, 1000, 0b00000000000, 1+(3*i), "END_LOOP", 2*(i+1)) #2
    pb.add_instruction(0, 0, 0, 0, 0b00010000000, 0, "CONT", 500*10**6)
pb.add_instruction(0, 0, 0, 0, 0b111100000000, 0, "STOP", 10) #4



pb.print_program()
rf_builder.update()


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