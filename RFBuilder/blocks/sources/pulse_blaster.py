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
    phaseWordBits = 30
    Fclk = 500 #MHz

    def __init__(self):
        self.instruction_list: list = []
        self.num_instructions: int = 0
        self.custom_update = True


        super().__init__("pulseblaster", [Port(PortDirection.OUTPUT, 2)])

    def add_instruction(self,phaseWord: float,freqWord: float,ttlStates: int,dataField: int,opcode: str,delayCounter: int):
        """
        Given the input parameters, generates a 128 bit wide instruction word (as a string) that can be read by the PBFSM.
        Returns a tuple containing the instruction word, the rounded frequency, and the rounded phase.

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
        if opcode not in PulseBlaster.opcodeDict:
            raise ValueError(f"Instruction {opcode} is not a known instruction word")
        freqWord = freqWord/16 #compensate for the upscaling of 16 in the polyphase DDS
        
        phaseIncr = round(freqWord*2**PulseBlaster.phaseWordBits/PulseBlaster.Fclk)#used to determin the frequency
        phaseOffset = round(2**PulseBlaster.phaseWordBits*phaseWord/360)
        instructionString=format(int(phaseOffset),"030b")+format(int(phaseIncr),"030b")+format(int(ttlStates),"012b")+format(int(dataField),"020b")+format(PulseBlaster.opcodeDict[opcode],"004b")+format(int(delayCounter),"032b") 
        self.instruction_list.append(instructionString)
        self.num_instructions += 1 


    def print_program(self):
        i = 0
        for instruction in self.instruction_list:
            phase = int(instruction[:30],2)
            phase = phase*360/(2**PulseBlaster.phaseWordBits)
            freq = int(instruction[30:60],2)
            freq = (freq*PulseBlaster.Fclk)/(2**PulseBlaster.phaseWordBits)
            ttlOuts = instruction[60:72]
            data = int(instruction[72:92],2)
            opcode = instruction[92:96]
            delay = instruction[96:128]
            print(f"Instruction {i}: phase = {phase}Deg, freq = {freq}MHz, ttl outputs = {ttlOuts}, data = {data}")
            i += 1


    def clean_program(self):
        self.instruction_list = []

    def update(self):
        bytes_array = bytearray()
        for instruction in self.instruction_list:
            lowerInstruction = int(instruction[:64],2)
            upperInstruction = int(instruction[64:],2)
            bytes_array += lowerInstruction.to_bytes(8, byteorder='little', signed=False)
            bytes_array += upperInstruction.to_bytes(8, byteorder='little', signed=False)

        return bytes_array, "api/pulseblaster"

    def __str__(self):
        output = ""
        output += f"Number of Instructions = {self.num_instructions}"
        for port in self.ports:
            output += f"\t\t{str(port)}\n"
        return output

    
