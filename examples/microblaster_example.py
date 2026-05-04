"""This file contains an example of using the MicroBlaster to generate a pulse sequence.
It is not necessarily a useful sequence, and is more to demonstrate the use of all the different instruction types."""

from RFBuilder import *
import matplotlib.pyplot as plt
import time

RUN = "SOFTWARE0"
TRIGGER = "SOFTWARE1"
RSTN = "SOFTWARE2"
MB_OUT0 = "SYZYGY_OUT7"
MB_OUT1 = "SYZYGY_OUT6"
MB_OUT2 = "SYZYGY_OUT5"
MB_OUT3 = "SYZYGY_OUT4"
TTL_IN0 = "SYZYGY_IN0"
TTL_IN1 = "SYZYGY_IN1"

board = RFSOC4x2()

rfbuilder = RFBuilder(board,"169.254.127.84",8080)

ub = MicroBlaster()
rfbuilder.add(ub)
dacs = rfbuilder.get_dacs()
rfbuilder.connect(ub,dacs[0])

rfbuilder.ttl.reset()

rfbuilder.ttl.connect(RUN,"MB_RUN") #allows a user to trigger 
rfbuilder.ttl.connect(RSTN,"MB_RSTN") #allows a user to reset the MicroBlaster using software
rfbuilder.ttl.connect("MB_FLAG0",MB_OUT0)
rfbuilder.ttl.connect("MB_FLAG1",MB_OUT1)
rfbuilder.ttl.connect("MB_FLAG2",MB_OUT2)
rfbuilder.ttl.connect("MB_FLAG3",MB_OUT3)

#below ANDs the TTL_IN0 (an external connection) signal and TRIGGER (a software controlled pin) signal, this is the connected to the MicroBlaster trigger line 
rfbuilder.ttl.connect([TTL_IN0,TRIGGER],"MB_TRIG")
rfbuilder.ttl.set_operation("MB_TRIG","AND") 

#Initiate a reset, this ensures if the MicroBlaster is in an infinite loop it will break out, allowing reprogramming. Additionally ensure run and trig are low
rfbuilder.ttl.update_state(RSTN,0)
rfbuilder.ttl.update_state(RSTN,1)
rfbuilder.ttl.update_state(RUN,0)
rfbuilder.ttl.update_state(TRIGGER,0)

#enable the sinc filter to minimise rolloff from DAC
rfbuilder.sinc_filters = 1

MHz = 1e6
GHz = 1e9
maxAmp = ub.get_max_amp()
holdFreq = ub.get_max_freq() #setting frequency to this value will cause it to hold the frequency from the previous instruction

ub.add_instruction(0b0011,500*MHz,0,maxAmp,100)
#cycle the phase between 0, 120, 240 repeated 10 times, each phase runs for a different time
ub.start_loop(0b0000,500*MHz,0,maxAmp,4,loops=10)
ub.long_delay(0b0000,500*MHz,120,maxAmp,300,mult=10) #each iteration of this instruction runs for 300*10=3000ns
ub.end_loop(0b0000,500*MHz,240,maxAmp,20)

#will change the frequency, then jump to a subroutine to sweep amp each time. Setting resync=1 ensures it always starts at phase=0
ub.jump_subroutine(0b0100,50*MHz,0,maxAmp,100,addr="amp_sweep",resync=1)
ub.jump_subroutine(0b0100,100*MHz,0,maxAmp,100,addr="amp_sweep",resync=1)
ub.jump_subroutine(0b0100,250*MHz,0,maxAmp,100,addr="amp_sweep",resync=1)
ub.jump_subroutine(0b0100,500*MHz,0,maxAmp,100,addr="amp_sweep",resync=1)
ub.jump_subroutine(0b0100,1*GHz,0,maxAmp,100,addr="amp_sweep",resync=1)

ub.wait(0b1000,15*MHz,0,int(maxAmp/2),0) #will set all fields to their given values, then wait until trigger goes high before continuing
ub.branch(0b0000,20*MHz,145,maxAmp,10,addr="end") #will jump directly to the end_program instruction

#infinite loop which will never be run because the above instruction branches past it
ub.add_instruction(0b0000,3.5*GHz,350,maxAmp,100,label="loop")
ub.branch(0b0000,35*MHz,350,maxAmp,100000000,addr = "loop")

#program execution will half here with the settings provided by this instruction
ub.end_program(0,0,0,0,4,label="end") 

#subroutine placed after the end program instruction which can be used to run an amplitude sweep at a given frequency
ub.add_instruction(0b0000,holdFreq,0,int(maxAmp/4),20,label="amp_sweep")
ub.add_instruction(0b0000,holdFreq,0,int(maxAmp/3),20)
ub.add_instruction(0b0000,holdFreq,0,int(maxAmp/2),20)
ub.add_instruction(0b0000,holdFreq,0,int(maxAmp/1),20)
ub.add_instruction(0b0000,holdFreq,0,int(maxAmp/2),20)
ub.add_instruction(0b0000,holdFreq,0,int(maxAmp/3),20)
ub.return_subroutine(0b0000,holdFreq,0,int(maxAmp/4),20)

#print the program
ub.print_program()

#set all ttl connections, and connect all blocks
rfbuilder.update()


#start the program running by pulsing the RUN pin
rfbuilder.ttl.update_state(RUN,2) 
time.sleep(5)
rfbuilder.ttl.update_state(TRIGGER,2) #if TTL_IN0 has not gone high after 5 seconds, the wait opcode is escaped broken using software


