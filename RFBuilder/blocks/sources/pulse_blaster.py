from fileinput import filename

from RFBuilder.control import ControlManager

from ..base import Source
from ..port import Port, PortDirection
from ...networking import send_http_data
import os
from enum import Enum



opcodeDict = {"CONT":0, #TODO: Convert into python equivilent of ENUM
                "STOP":1,
                "LOOP":2,
                "END_LOOP":3,
                "JSR":4,
                "RTS":5,
                "BRANCH":6,
                "LONG_DELAY":7,
                "WAIT":8}

class PBInstruction():
    instructionLength = 256 #in bits
    Fclk = 500*10**6 #Hz
    phasehopLen = 1
    resyncLen = 1
    ampLen = 16
    phaseLen = 48
    freqLen = phaseLen
    ttlLen=12
    opcodeLen = 4
    delayLen = 32
    dataLen = 20 

    phasehopSB = instructionLength - (phasehopLen+resyncLen+ampLen+phaseLen+freqLen+ttlLen+opcodeLen+delayLen+dataLen)
    resyncSB = phasehopSB + phasehopLen
    ampSB = resyncSB + resyncLen
    phaseSB = ampSB + ampLen
    freqSB = phaseSB + phaseLen
    ttlSB = freqSB + freqLen
    dataSB = ttlSB + ttlLen
    opcodeSB = dataSB + dataLen
    delaySB = opcodeSB + opcodeLen
    addrWidth = 17 #TODO: have a check to confirm if more then the max possible instructions are written
    
    def __init__(self, opcode:str, ttl:int, freq:float, phase:float, amp:int, delay:int, data:int, resync:bool,phasehop:bool,instructionNum:int):
        self.opcode = opcode
        self.ttl = ttl
        self.freq = freq
        self.phase = phase
        self.amp = amp
        self.delay = delay
        self.data = data
        self.resync = resync
        self.phasehop = phasehop
        self.instructionNum = instructionNum
    
    def encode_instruction(self):
        freq = self.freq/16 #compensate for the upscaling of 16 in the polyphase DDS
        phasehop = 1 - int(self.phasehop) #for a user, a 1 should indicate phasehop functionality enabled, however it goes to a CE pin so needs to be inverted 
        resync = 1 - int(self.resync) #flips 1 to 0 and 0 to 1, done as the dds has an active low reset
        delay = (self.delay-2) / 2 #each clock tick is 2ns, and the count value is how many clock ticks to wait, so a delay of 1000 nanoseconds is 499 clock ticks
        phaseLen = self.phaseLen
        Fclk = self.Fclk
        instructionLength = PBInstruction.instructionLength
        phasehopSB = PBInstruction.phasehopSB

        phaseIncr = round(freq*2**phaseLen/Fclk) #used to determin the frequency
        phaseOffset = round((2**phaseLen)*self.phase/360)
    
        #lenTotal = self._phasehopLen + self._resyncLen + self._ampLen + self._phaseLen + self._freqLen + self._ttlLen + self._dataLen + self._opcodeLen + self._delayLen
        instructionString = ""
        
        if(phasehopSB < 0): #check the combined lengths of the fields doesn't exceed the instruction length, this length difference will be the start bit for the phasehop flag
            raise ValueError(f"Defined instruction bus width {PBInstruction.instructionLength} shorter then actual instruction length")
        else: #0 pad up to the full bus width
            for i in range(phasehopSB):
                instructionString += "0"
        instructionString += format(int(phasehop),f"0{self.phasehopLen}b")
        instructionString += format(int(resync),f"0{self.resyncLen}b")
        instructionString += format(int(self.amp),f"0{self.ampLen}b")
        instructionString += format(int(phaseOffset),f"0{self.phaseLen}b")
        instructionString += format(int(phaseIncr),f"0{self.freqLen}b")
        instructionString += format(int(self.ttl),f"0{self.ttlLen}b")
        instructionString += format(int(self.data),f"0{self.dataLen}b")
        instructionString += format(opcodeDict[self.opcode],f"0{self.opcodeLen}b")
        instructionString += format(int(delay),f"0{self.delayLen}b")

        instructionBytes = bytearray()
        for i in range(int(instructionLength/8)-1,-1,-1): 
            instructionBytes += int(instructionString[i*8:(i+1)*8],2).to_bytes(1,"little",signed = False)

        return instructionBytes

class PulseBlaster(Source):
    Fclk = PBInstruction.Fclk
    freqLen = PBInstruction.freqLen
    addrWidth = PBInstruction.addrWidth
    phaseLen = PBInstruction.phaseLen

    freqRes = Fclk*16/(2**freqLen) #frequency resolution in Hz, multiplied by 16 due to sample rate upscaling
    phaseRes = 360/(2**phaseLen) #phase offset resolution in degrees
    maxAmp = (2**15)-1
    maxFreq = 16*((2**phaseLen)-1)*Fclk/(2**phaseLen) #multiplied by 16 to account for scaling
    maxPhase = 360*(2**phaseLen-1)/(2**phaseLen)

    def __init__(self):
        self.instructionList: list[PBInstruction] = []
        self.numInstructions: int = 0
        
        super().__init__("pulseblaster", [Port(PortDirection.OUTPUT, 2)])
        self.custom_update = True

    def register_block(self, ip: str = "", port: int = 0, index: int = 0,ttl: ControlManager = None):
        self.ip = ip
        self.port = port

        self.pins = ttl.pins.pulseblaster

        ttl.connect(ttl.pins.reserved[0], "PB_RUN") # Connect the "PULSE ON BOOT" pin to PB_RUN
        ttl.connect(ttl.pins.reserved[2], "PB_RSTN") # Connect the "HIGH" pin to PB_RSTN for always off
        ttl.connect(["KEY0", "SOFTWARE0"], "PB_TRIG")


        return super().register_block()
    
    def gen_instruction(self, opcode:str, ttl:int,  freq:float, phase:float, amp:int, delay:int, data:int, resync:bool, instrucNum:int) -> PBInstruction:
        """_summary_

        Args:
            opcode (str): _description_
            ttl (int): _description_
            freq (float): _description_
            phase (float): _description_
            amp (int): _description_
            delay (int): _description_
            data (int, optional): _description_. Defaults to 0.
            resync (bool, optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_
            ValueError: _description_

        Returns:
            instruction (PBInstruction): _description_
        """
        self.dirty = True
        maxAmp = PulseBlaster.maxAmp
        maxFreq = PulseBlaster.maxFreq
        maxPhase = PulseBlaster.maxPhase

        #Update optionalInputs to reflect any input by the user
        if opcode not in opcodeDict:
            raise ValueError(f"Instruction {opcode} is not a known instruction word")

        if int(ttl) != ttl:
            raise ValueError("ttl input field should be an int")
                
        if not (0 <= freq <= maxFreq):
            raise ValueError(f"freq input field should be between 0 and {maxFreq}")

        if not(0 <= phase <= maxPhase):
            raise ValueError(f"phase input field should be between 0 {maxPhase}")

        if not(0<= amp <= maxAmp):
            raise ValueError(f"amp must be in the range of -{maxAmp} to {maxAmp}")
        if int(amp)!=amp:
            raise ValueError("amp input field must be an integer")

        if(delay%2 != 0):
            raise ValueError("Delay must be an integer multiple of 2")
        if(delay < 4):
            raise ValueError("Delay must be at least 4ns")

        if((opcode == "LONG_DELAY") & (data!=0)): #done so dataField*delay = total delay length
            data = data - 1

        if resync == None: #if the user does not input a value, default to a value based on opcode
            if(opcode == "STOP"):
                resync = 1
            else:
                resync = 0
            
        if (opcode == "STOP") and (resync == 0):
            print("WARNING: Resync Flag set to 0 for STOP opcode. This may lead to an inconsistent starting phase across multiple runs of the program.")

        phasehop = 0 #TODO: Reimpliment once single cycle instructions works
        instruction = PBInstruction(opcode,ttl,freq,phase,amp,delay,data,resync,phasehop,instrucNum)
        self.numInstructions += 1 
        return instruction

    def add_instruction(self, opcode:str, ttl:int,  freq:float, phase:float, amp:int, delay:int, data:int = 0, resync:bool = None):
       instruction = self.gen_instruction(opcode,ttl,freq,phase,amp,delay,data,resync,self.numInstructions)
       self.instructionList.append(instruction)
       return instruction.instructionNum
    
    def prepend_instruction(self, opcode:str, ttl:int,  freq:float, phase:float, amp:int, delay:int, data:int = 0, resync:bool = None):
        instruction = self.gen_instruction(opcode,ttl,freq,phase,amp,delay,data,resync,0)
        self.instructionList.insert(0,instruction)
        for instruc in self.instructionList:
            instruc.instructionNum +=1
        return instruction.instructionNum

    def print_program(self,mode = "user"):
        #TODO: reimpliment phasehop
        for entry in self.instructionList:
            print(f"Instruction {entry.instructionNum}: opcode = {entry.opcode}, ttl = {entry.ttl}, freq = {entry.freq}Hz, phase = {entry.phase}deg, amp = {entry.amp}, delay = {entry.delay}ns, data = {entry.data}, resync = {entry.resync}\n")
        
    def clean_program(self):
        """Removes all instructions from the current program."""
        self.dirty = True
        self.numInstructions = 0
        self.instructionList = []

    def save_program(self,filename: str):
        """
        Save program to a text file in the current working directory which can later be reloaded using loadprogram.

        :param filename: Name of the file to save the program in. Include file extension in filename
        :type filename: string
        """
        #workingDirectory=os.getcwd()
        fileHandler = open(filename,"w")
        for entry in self.instructionList:
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
            print(f"loadprogram was unable to find {filename}")
            return -1
        programList = fileHandler.readlines()
        self.instructionList = programList

    def get_freq_res(self):
        return PulseBlaster.freqRes

    def get_phase_res(self):
        return PulseBlaster.phaseRes
    
    def get_amp_max(self):
        return PulseBlaster.maxAmp
    
    def get_freq_max(self):
        return PulseBlaster.maxFreq
    
    def get_phase_max(self):
        return PulseBlaster.maxPhase

    def update(self):
        bytes_array = bytearray()
        stopPresent = 0 #TODO: make sure this is still checked
        for instruction in self.instructionList:
            if(instruction.opcode == "STOP"):
                stopPresent = 1 
            bytes_array += instruction.encode_instruction()
        if(stopPresent == 0):
            raise ValueError("PulseBlaster program must contain a stop command")
        return bytes_array, "api/pulseblaster"

    def __str__(self):
        output = ""
        output += f"[PulseBlaster] Number of Instructions = {self.numInstructions}\n"
        for port in self.ports:
            output += f"\t\t{str(port)}\n"
        return output
    
    def _generate_coe(self,filename, awidth, offset = 0, mask = False, ctrl = False, include_end_command = True):
        if(offset%4 != 0): #leaving this in for now since this is true for the AXI traffic generator, this doens't need to hold for DRAM but DRAM only needs the data file not the address file so it doesn't matter anyway
            raise ValueError("Input variable 'offset' must be an integer mutliple of 4")
        if(awidth < 0):
            raise Exception(f"awidth value must be greater than 0")
        workingDirectory=os.getcwd()
        addressFile=open(os.path.join(workingDirectory+filename+"_address.coe"),"w")
        dataFile=open(os.path.join(workingDirectory+filename+"_data.coe"),"w")
        addressFile.write("memory_initialization_radix = 2;\n memory_initialization_vector = \n")
        dataFile.write("memory_initialization_radix = 2;\n memory_initialization_vector = \n")
        
        addrNum = offset
        for instr in self.instructionList:
            for i in range(int(PulseBlaster.instructionLength/32)): #this converts each instruction into 32 bit chunks
                flippedData = instr[::-1]
                scaledData = flippedData[i*32:(i+1)*32]
                scaledData = scaledData[::-1] #flip back
                dataFile.write(f"{scaledData}\n") #have to start from the end of the list since it is the lsb
                addressFile.write(f"{format(addrNum,f"0{awidth}b")}\n")
                addrNum += 4 #move 4 bytes over in memory

    def _generate_testbenchfile(self,filename):
        addressPointer=0
        workingDirectory = os.getcwd()
        opcode=self.instructionList[0][PulseBlaster.opcodeSB : PulseBlaster.opcodeSB+PulseBlaster.opcodeLen]   
        unwrappedFile = open(os.path.join(workingDirectory+filename),"w")
        unwrappedFile.write("1,1,0000000000000000,000000000000000000000000000000,000000000000000000000000000000,000000000000,0\n") #0 pad the start based on reset states
        loopStack = [[(2**self.addrBits)-1,0]] #first address is at the very end so when it is checked it always returns not used
        loopPointer = 0
        rtsAddress = 0
        counter = 0
        while (addressPointer < len(self.instructionList)):
            currentInstruction = self.instructionList[addressPointer]
            opcode = currentInstruction[PulseBlaster.opcodeSB : PulseBlaster.opcodeSB+PulseBlaster.opcodeLen]
            opcode = int(opcode,2)
            delayCounter = int(currentInstruction[self.delaySB : self.delaySB+self.delayLen],2)
            waitFlag=0

            if(opcode == self.opcodeDict["CONT"]):
                addressPointer += 1
            elif (opcode == self.opcodeDict["STOP"]):
                addressPointer = len(self.instructionList)
            elif (opcode == self.opcodeDict["LOOP"]):
                if(addressPointer != loopStack[loopPointer][0]):
                    if(loopStack[loopPointer][0] == 2**self.addrBits-1):
                        loopStack[loopPointer][0] = addressPointer
                        loopStack[loopPointer][1] = int(currentInstruction[self.dataSB : self.dataSB+self.dataLen],2)
                    else:
                        loopPointer += 1
                        loopStack.append([addressPointer,int(currentInstruction[self.dataSB : self.dataSB+self.dataLen],2)])
                addressPointer += 1
            elif (opcode == self.opcodeDict["END_LOOP"]):
                loopStack[loopPointer][1] -= 1
                if(loopStack[loopPointer][1] == 0):
                    addressPointer +=1
                    if(len(loopStack)>1):
                        loopStack.pop(-1) #remove that entry from the loopStack
                        loopPointer -= 1
                    else:
                        loopStack = [[2**self.addrBits-1,0]]
                        loopPointer = 0
                else:
                    addressPointer = int(currentInstruction[self.dataSB : self.dataSB+self.dataLen],2) #should have the loop address in the data field
            elif (opcode == self.opcodeDict["JSR"]):
                rtsAddress = addressPointer+1
                addressPointer = int(currentInstruction[self.dataSB : self.dataSB+self.dataLen],2) #should have the subroutine address in the data field
            elif (opcode == self.opcodeDict["RTS"]):
                addressPointer = rtsAddress
            elif (opcode == self.opcodeDict["BRANCH"]):
                addressPointer = int(currentInstruction[self.dataSB : self.dataSB+self.dataLen],2) #should have the branch address in the data field
            elif (opcode == self.opcodeDict["LONG_DELAY"]):
                addressPointer += 1 #here there is just a longer delay which the tb currently doesn't check since it is an internal param
                delayCounter = delayCounter * int(currentInstruction[self.dataSB : self.dataSB+self.dataLen],2)
            elif (opcode == self.opcodeDict["WAIT"]):
                addressPointer += 1 #since this is just getting the expected output of the instructions no need to do anything apart from incriment counter
                waitFlag = 1
            else:
                raise ValueError(f"The instruction at address {addressPointer} does not contain a valid opcode: {opcode}")

            ampOutput = currentInstruction[self.ampSB : self.ampSB+self.ampLen]
            resyncFlag = currentInstruction[self.resyncSB : self.resyncSB+self.resyncLen]
            phasehopFlag = currentInstruction[self.phasehopSB : self.phasehopSB+self.phasehopLen]
            phaseOutput = currentInstruction[self.phaseSB : self.phaseSB+self.phaseLen]
            freqOutput = currentInstruction[self.freqSB : self.freqSB+self.freqLen] #account for downscaling from PulseBlaster
            ttlOutput = currentInstruction[self.ttlSB : self.ttlSB+self.ttlLen]
            #print(delayCounter)
            if(waitFlag == 0):
                for i in range((delayCounter+1)): #plus 1 because for a delay of 5 it should count from 0 up to 5 before wrapping around, divide by 2 since the input is ns not clock cycles
                    unwrappedFile.write(f"{phasehopFlag},{resyncFlag},{ampOutput},{phaseOutput},{freqOutput},{ttlOutput},{waitFlag}\n")
            else:
                unwrappedFile.write(f"{phasehopFlag},{resyncFlag},{ampOutput},{phaseOutput},{freqOutput},{ttlOutput},{waitFlag}\n")
        unwrappedFile.close()
