from ..base import Source
from ..port import Port, PortDirection

import numpy as np

class PulseBlaster(Source):
    opcodeDict = {"CONT":0,
                "STOP":1,
                "LOOP":2,
                "END_LOOP":3,
                "JSR":4,
                "RTS":5,
                "BRANCH":6,
                "LONG_DELAY":7,
                "WAIT":8}
    instructionLength = 128 #in bits
    phaseWordBits = 30
    Fclk = 500 #MHz
    def __init__(self):
        self.instruction_list: list = []
        self.num_instructions: int = 0
        super().__init__("pulseblaster", [Port(PortDirection.OUTPUT, 2)])
        self.custom_update = True

    def add_instruction(self,phasehopFlag: bool,resyncFlag: bool,phaseWord: float,freqWord: float,ttlStates: int,dataField: int,opcode: str,delayCounter: int):
        """
        Given the input parameters, create the 128 bit wide instruction and adds it to the program which can be sent to the pulse blaster.

        :param phasehopFlag: Set to true if the frequency word should be used to perform a global phase hop.
        :type phasehopFlag: bool
        :param resyncFlag: Set to true if you want to reset the phase accumulation register of the DDS back to 0
        :type resyncFlag: bool
        :param phaseWord: Desired phase offset in degrees, will be rounded based on input clock frequency
        :type phaseWord: float
        :param frequWord: Desired frequency in MHz, this will be converted to the required phase impliment to calculate that frequency
        :type frequWord: float
        :param ttlStates: Input as a binary format, each bit represents a particual ttl line to turn on or off based on the bit value. Only 12 bits avalible
        :type ttlStates: int
        :param dataField: Data field, input as either a int or binary value depending on which makes most sense for the given opcode
        :type dataField: int
        :param opcode: Used to spesify the opcode for the instruction, can be one of the 8 opcodes as given in the opcode dictionaty
        :type opcode: str
        :param delayCounter: How many clock cycles to wait before executing the next instruction
        :type delayCounter: int
        :param Fclk: The frequency that the DDS connected to the PBFSM runs at in MHz. Used to calculate phase incrument and offset
        :type Fclk: float
        """
        self.dirty = True
        if opcode not in PulseBlaster.opcodeDict:
            raise ValueError(f"Instruction {opcode} is not a known instruction word")
        freqWord = freqWord/16 #compensate for the upscaling of 16 in the polyphase DDS
        phaseWord = phaseWord / 4 #compensate for shifting done by the pulseblaster
        phaseIncr = round(freqWord*2**PulseBlaster.phaseWordBits/PulseBlaster.Fclk)#used to determin the frequency
        phaseOffset = round(2**PulseBlaster.phaseWordBits*phaseWord/360)
        instructionString=format(int(phasehopFlag),"01b")+format(int(resyncFlag),"01b")+format(int(phaseOffset),"028b")+format(int(phaseIncr),"030b")+format(int(ttlStates),"012b")+format(int(dataField),"020b")+format(PulseBlaster.opcodeDict[opcode],"004b")+format(int(delayCounter),"032b") 
        self.instruction_list.append(instructionString)
        self.num_instructions += 1 


    def print_program(self):
        i = 0
        for instruction in self.instruction_list:
            phaseHopFlag = bool(int(instruction[0]))
            resyncFlag = bool(int(instruction[1]))
            phase = int(instruction[2:30],2)
            phase = phase*360/(2**PulseBlaster.phaseWordBits)*4
            freq = int(instruction[30:60],2)
            freq = (freq*PulseBlaster.Fclk)/(2**PulseBlaster.phaseWordBits)*16
            ttlOuts = instruction[60:72]
            data = int(instruction[72:92],2)
            opcode = int(instruction[92:96])
            opcode = next((k for k, v in PulseBlaster.opcodeDict.items() if v == opcode), None)
            delay = int(instruction[96:128],2)
            print(f"Instruction {i}: phase hop flag = {phaseHopFlag}, resync = {resyncFlag}, phase = {phase}Deg, freq = {freq}MHz, ttl outputs = {ttlOuts}, data = {data}, opcode = {opcode}, delay = {delay} clock cycles\n")
            i += 1

    def clean_program(self):
        self.dirty = True
        self.instruction_list = []


    def trigger(self):
        print("PulseBlaster.trigger() is not currently implimented")

    def run(self):
        print("PulseBlaster.run() is not currently implimented")

    def reset(self):
        print("PulseBlaster.reset() is not currently implimented")

    def update(self):
        bytes_array = bytearray()
        for instruction in self.instruction_list:
            #instruction = instruction[::-1]
            for i in range(int(PulseBlaster.instructionLength/8)-1,-1,-1): 
                #print(i)
                bytes_array += int(instruction[i*8:(i+1)*8],2).to_bytes(1,"little",signed = False)
        
        return bytes_array, "api/pulseblaster"

    def __str__(self):
        output = ""
        output += f"[PulseBlaster] Number of Instructions = {self.num_instructions}\n"
        for port in self.ports:
            output += f"\t\t{str(port)}\n"
        return output

    
