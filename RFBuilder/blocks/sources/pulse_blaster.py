from ..base import Source
from ..port import Port, PortDirection
from ...networking import send_http_data
import os


class PulseBlaster(Source):
    _opcodeDict = {"CONT":0,
                "STOP":1,
                "LOOP":2,
                "END_LOOP":3,
                "JSR":4,
                "RTS":5,
                "BRANCH":6,
                "LONG_DELAY":7,
                "WAIT":8}
    _instructionLength = 256 #in bits
    _phaseWordBits = 32
    _Fclk = 500 #MHz
    _phasehopLen = 1
    _resyncLen = 1
    _ampLen = 16
    _phaseLen = 32
    _freqLen = _phaseLen
    _ttlLen=12
    _opcodeLen = 4
    _delayLen = 32
    _dataLen = 20

    _phasehopSB = _instructionLength - (_phasehopLen+_resyncLen+_ampLen+_phaseLen+_freqLen+_ttlLen+_opcodeLen+_delayLen+_dataLen)
    _resyncSB = _phasehopSB + _phasehopLen
    _ampSB = _resyncSB + _resyncLen
    _phaseSB = _ampSB + _ampLen
    _freqSB = _phaseSB + _phaseLen
    _ttlSB = _freqSB + _freqLen
    _dataSB = _ttlSB + _ttlLen
    _opcodeSB = _dataSB + _dataLen
    _delaySB = _opcodeSB + _opcodeLen
    
    freqRes = _Fclk*16/(2**_freqLen) #frequency resolution in MHz, multiplied by 16 due to sample rate upscaling
    phaseRes = 360/(2**_phaseLen) #phase offset resolution in degrees
    def __init__(self):
        self.instruction_list: list = []
        self.num_instructions: int = 0
        pins = {"run":0,
                "trigger":0,
                "resetn":1,
                     }
        
        super().__init__("pulseblaster", [Port(PortDirection.OUTPUT, 2)],pins)
        self.custom_update = True

    def register_block(self, ip: str = "", port: int = 0):
        self.ip = ip
        self.port = port

        return super().register_block()
    
    def add_instruction(self,phasehopFlag: bool,resyncFlag: bool, ampWord: int,  phaseWord: float,freqWord: float,ttlStates: int,dataField: int,opcode: str,delayCounter: int):
        """
        Given the input parameters, create the 128 bit wide instruction and adds it to the program which can be sent to the pulse blaster.
        
        :param phasehopFlag: Set to true if the frequency word should be used to perform a global phase hop.
        :type phasehopFlag: bool
        :param resyncFlag: Set to true if you want to reset the phase accumulation register of the DDS back to 0
        :type resyncFlag: bool
        :param ampWord: Amplitude of the output wave, from 0 to 65535 with 0 being min and 65535 being max
        :type ampWord: int
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
        :param _Fclk: The frequency that the DDS connected to the PBFSM runs at in MHz. Used to calculate phase incrument and offset
        :type _Fclk: float
        """
        self.dirty = True
        if opcode not in PulseBlaster._opcodeDict:
            raise ValueError(f"Instruction {opcode} is not a known instruction word")
        
        if(delayCounter%2 != 0):
            raise ValueError("Delay must be an integer multiple of 2")
        elif(delayCounter < 4):
            raise ValueError("Delay must be at least 4ns")
        
        if((0 > ampWord) or ((2**16)-1) < ampWord):
            raise ValueError("ampWord must be in the range of 0 to 65535")
        
        freqWord = freqWord/16 #compensate for the upscaling of 16 in the polyphase DDS
        phasehopFlag = 1 - int(phasehopFlag) #for a user, a 1 should indicate phasehop functionality enabled, however it goes to a CE pin so needs to be inverted 
        resyncFlag = 1 - int(resyncFlag) #flips 1 to 0 and 0 to 1, done as the dds has an active low reset
        delayCounter = (delayCounter-2) / 2 #each clock tick is 2ns, and the count value is how many clock ticks to wait, so a delay of 1000 nanoseconds is 499 clock ticks
        
        phaseIncr = round(freqWord*2**PulseBlaster._phaseWordBits/PulseBlaster._Fclk) #used to determin the frequency
        phaseOffset = round((2**PulseBlaster._phaseWordBits)*phaseWord/360) 
        
        lenTotal = self._phasehopLen + self._resyncLen + self._ampLen + self._phaseLen + self._freqLen + self._ttlLen + self._dataLen + self._opcodeLen + self._delayLen
        instructionString = ""
        
        if(self._phasehopSB < 0): #check the combined lengths of the fields doesn't exceed the instruction length, this length difference will be the start bit for the phasehop flag
            raise ValueError("Defined bus width for instruction (_instructionLength) shorter then actual instruction length")
        else: #0 pad up to the full bus width
            for i in range(self._phasehopSB):
                instructionString += "0"
        instructionString += format(int(phasehopFlag),f"0{self._phasehopLen}b")
        instructionString += format(int(resyncFlag),f"0{self._resyncLen}b")
        instructionString += format(int(ampWord),f"0{self._ampLen}b")
        instructionString += format(int(phaseOffset),f"0{self._phaseLen}b")
        instructionString += format(int(phaseIncr),f"0{self._freqLen}b")
        instructionString += format(int(ttlStates),f"0{self._ttlLen}b")
        instructionString += format(int(dataField),f"0{self._dataLen}b")
        instructionString += format(PulseBlaster._opcodeDict[opcode],f"0{self._opcodeLen}b")
        instructionString += format(int(delayCounter),f"0{self._delayLen}b")
         
        self.instruction_list.append(instructionString)
        self.num_instructions += 1 


    def print_program(self,mode = "user"):
        """
        Prints out all instructions in the current program.
        
        :param mode: Determins the format of the printed instruction
        :type mode: str
        """
        i = 0
        for instruction in self.instruction_list:
            if (mode == "user"):
                phaseHopFlag = not bool(int(instruction[self._phasehopSB : self._phasehopSB + self._phasehopLen])) #inverted back into user friendly value
                resyncFlag = not bool(int(instruction[self._resyncSB : self._resyncSB + self._resyncLen])) #inverted back into user friendly value
                amp = int(instruction[self._ampSB : self._ampSB + self._ampLen])
                phase = int(instruction[self._phaseSB : self._phaseSB + self._phaseLen],2)
                phase = phase*360/(2**PulseBlaster._phaseWordBits)*4

                freq = int(instruction[self._freqSB : self._freqSB + self._freqLen],2)
                freq = (freq*PulseBlaster._Fclk)/(2**PulseBlaster._phaseWordBits)*16

                ttlOuts = instruction[self._ttlSB : self._ttlSB + self._ttlLen]
                data = int(instruction[self._dataSB : self._dataSB + self._dataLen],2)
                opcode = int(instruction[self._opcodeSB : self._opcodeSB + self._opcodeLen],2)
                for key in self._opcodeDict.keys():
                    if self._opcodeDict[key] == opcode:
                        opcode = key
                delay = int(instruction[self._delaySB : self._delaySB + self._delayLen],2)
                print(f"Instruction {i}: phase hop flag = {phaseHopFlag}, resync = {resyncFlag}, amp = {amp}, phase = {phase}Deg, freq = {freq}MHz, ttl outputs = {ttlOuts}, data = {data}, opcode = {opcode}, delay = {delay} clock cycles\n")
            
            elif (mode == "bin"):
                print(f"Instruction {i}: {instruction}")
            elif (mode == "hex"):
                instructionString = ""
                for j in range(int(self._instructionLength/32)):
                    currentString = format(int(instruction[j*32 : (j+1)*32],2),"08X")
                    instructionString += currentString
                print(f"Instruction {i}: {instructionString}")
            elif (mode == "dec"):
                instructionString = ""
                for j in range(int(self._instructionLength/32)):
                    currentString = format(int(instruction[j*32 : (j+1)*32],2),"010d")
                    instructionString += currentString
                print(f"Instruction {i}: {instructionString}")
            else:
                print("Unknown print mode requested")
            i += 1

    def clean_program(self):
        """Removes all instructions from the current program."""
        self.dirty = True
        self.num_instructions = 0
        self.instruction_list = []

    def save_program(self,filename: str):
        """
        Save program to a text file in the current working directory which can later be reloaded using load_program.

        :param filename: Name of the file to save the program in. Include file extension in filename
        :type filename: string
        """
        #workingDirectory=os.getcwd()
        fileHandler = open(filename,"w")
        for entry in self.instruction_list:
            fileHandler.write(entry+"\n")
        fileHandler.close()

    def load_program(self, filename: str):
        """
        Load a program from a textfile of the name "programName", make sure to include file extention.

        :param filename: Name of the file containing the program. Include file extension in filename
        :type filename: string
        """
        try:
            fileHandler = open(filename,"r")
        except FileNotFoundError:
            print(f"load_program was unable to find {filename}")
            return -1
        programList = fileHandler.readlines()
        self.instruction_list = programList

    def update(self):
        bytes_array = bytearray()
        stopPresent = 0
        for instruction in self.instruction_list:
            if(int(instruction[self._opcodeSB : self._opcodeSB + self._opcodeLen],2) == PulseBlaster._opcodeDict["STOP"]):
                stopPresent = 1
            for i in range(int(PulseBlaster._instructionLength/8)-1,-1,-1): 
                bytes_array += int(instruction[i*8:(i+1)*8],2).to_bytes(1,"little",signed = False)
        if(stopPresent == 0):
            raise ValueError("PulseBlaster program must contain a stop command")
        return bytes_array, "api/pulseblaster/instructions"

    def __str__(self):
        output = ""
        output += f"[PulseBlaster] Number of Instructions = {self.num_instructions}\n"
        for port in self.ports:
            output += f"\t\t{str(port)}\n"
        return output

    
