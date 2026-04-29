from RFBuilder.control import ControlManager
from ..base import Source
from ..port import Port, PortDirection
from ...networking import send_http_data
import os
from enum import Enum
import pickle

class OPCODE(Enum):
    CONT = 0
    STOP = 1
    LOOP = 2
    END_LOOP = 3
    JSR = 4
    RTS = 5
    BRANCH = 6
    LONG_DELAY = 7
    WAIT = 8

class MBInstruction():
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

    delaySB = 0
    opcodeSB = delayLen
    dataSB = opcodeSB+opcodeLen
    ttlSB = dataSB + dataLen
    freqSB = ttlSB + ttlLen
    phaseSB = freqSB + freqLen
    ampSB = phaseSB + phaseLen
    resyncSB = ampSB + ampLen
    phasehopSB = resyncSB + resyncLen
    addrWidth = 17 #TODO: have a check to confirm if more then the max possible instructions are written
    
    def __init__(self, opcode:OPCODE, ttl:int, freq:float, phase:float, amp:int, delay:int, data:int|str, resync:bool,phasehop:bool,instructionNum:int,label:str):
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
        self.label = label
    
    def encode_instruction(self,labelDict):
        phaseLen = self.phaseLen
        Fclk = self.Fclk
        instructionLength = MBInstruction.instructionLength
        phasehopSB = MBInstruction.phasehopSB
        
        freq = self.freq/16 #compensate for the upscaling of 16 in the polyphase DDS
        phasehop = 1 - int(self.phasehop) #for a user, a 1 should indicate phasehop functionality enabled, however it goes to a CE pin so needs to be inverted 
        resync = 1 - int(self.resync) #flips 1 to 0 and 0 to 1, done as the dds has an active low reset
        delay = (self.delay-2) / 2 #each clock tick is 2ns, and the count value is how many clock ticks to wait, so a delay of 1000 nanoseconds is 499 clock ticks
        amp = self.amp
        ttl = self.ttl
        data = self.data if isinstance(self.data,int) else labelDict[self.data] #check to see if data is an int or a label for an instruction
        opcode = self.opcode
        phaseIncr = round(freq*2**phaseLen/Fclk) #used to determin the frequency
        phaseOffset = round((2**phaseLen)*self.phase/360)
    
        if phasehopSB < 0: #check the combined lengths of the fields doesn't exceed the instruction length
            raise ValueError(f"Defined instruction bus width {instructionLength} shorter then actual instruction length")
        
        # Build instruction as a single integer using bit shifts
        instruction = 0
        instruction |= int(phasehop) << MBInstruction.phasehopSB
        instruction |= int(resync) << MBInstruction.resyncSB
        instruction |= int(amp) << MBInstruction.ampSB
        instruction |= int(phaseOffset) << MBInstruction.phaseSB
        instruction |= int(phaseIncr) << MBInstruction.freqSB
        instruction |= int(ttl) << MBInstruction.ttlSB
        instruction |= int(data) << MBInstruction.dataSB
        instruction |= int(opcode.value) << MBInstruction.opcodeSB
        instruction |= int(delay) << MBInstruction.delaySB
        
        # Convert directly to bytes in little-endian format
        instructionBytes = instruction.to_bytes(instructionLength // 8, byteorder='little', signed=False)
        return instructionBytes

class MicroBlaster(Source):
    Fclk = MBInstruction.Fclk
    freqLen = MBInstruction.freqLen
    addrWidth = MBInstruction.addrWidth
    phaseLen = MBInstruction.phaseLen
    delayLen = MBInstruction.delayLen
    dataLen = MBInstruction.dataLen
    ampLen = MBInstruction.ampLen
    ttlLen = MBInstruction.ttlLen
    

    freqRes = Fclk*16/(2**freqLen) #frequency resolution in Hz, multiplied by 16 due to sample rate upscaling
    phaseRes = 360/(2**phaseLen) #phase offset resolution in degrees
    maxAmp = (2**(ampLen-1))-1
    maxFreq = 16*((2**phaseLen)-1)*Fclk/(2**phaseLen) #multiplied by 16 to account for scaling
    maxPhase = 360*(2**phaseLen-1)/(2**phaseLen)
    maxDelay = 2*(2**delayLen-1) + 2
    maxData = 2**dataLen-1
    maxTtl = 2**ttlLen-1

    def __init__(self):
        self.instructionList: list[MBInstruction] = []
        self.numInstructions: int = 0
        self.labelDict: dict[str:int] = {}
        
        super().__init__("microblaster", [Port(PortDirection.OUTPUT, 2)])
        self.custom_update = True

    def register_block(self, ip: str = "", port: int = 0, index: int = 0,ttl: ControlManager = None):
        self.ip = ip
        self.port = port

        self.pins = ttl.pins.microblaster

        ttl.connect(ttl.pins.reserved[0], "MB_RUN") # Connect the "PULSE ON BOOT" pin to MB_RUN
        ttl.connect(ttl.pins.reserved[2], "MB_RSTN") # Connect the "HIGH" pin to MB_RSTN for always off
        ttl.connect(["KEY0", "SOFTWARE0"], "MB_TRIG")


        return super().register_block()
    
    def gen_instruction(self, opcode:str, ttl:int,  freq:float, phase:float, amp:int, delay:int, data:int|str, resync:bool, prepend:bool, label:str) -> int:
        self.dirty = True
        maxAmp = MicroBlaster.maxAmp
        maxFreq = MicroBlaster.maxFreq
        maxPhase = MicroBlaster.maxPhase
        maxData = MicroBlaster.maxData
        maxDelay = MicroBlaster.maxDelay
        maxTtl = MicroBlaster.maxTtl

        #Update optionalInputs to reflect any input by the user
        if opcode not in OPCODE:
            raise ValueError(f"Instruction {opcode} is not a known instruction word")

        if int(ttl) != ttl:
            raise ValueError("ttl input field should be an int")
        if not(0 <= ttl <= maxTtl):
            raise ValueError(f"ttl input field must be between 0 and {maxTtl}")
                
        if not (0 <= freq <= maxFreq):
            raise ValueError(f"freq input field should be between 0 and {maxFreq}")

        if not(0 <= phase <= maxPhase):
            raise ValueError(f"phase input field should be between 0 {maxPhase}")

        if not(0<= amp <= maxAmp):
            raise ValueError(f"amp must be in the range of -{maxAmp} to {maxAmp}")
        if int(amp)!=amp:
            raise ValueError("amp input field must be an integer")

        if not isinstance(data,(str,int)):
            raise ValueError("data input field must be an integer of a string")
        if isinstance(data,int):
            if not(0<=data<=maxData):
                raise ValueError(f"data input field must be beterrn 0 and {maxData}")
        
        if not(0<=delay<=maxDelay):
            raise ValueError(f"delay input field must be between 0 and {maxDelay}")
        if(delay%2 != 0):
            raise ValueError("Delay must be an integer multiple of 2")
        if(opcode != OPCODE.WAIT):
            if(delay < 4):
                raise ValueError("Delay must be at least 4ns")

        if((opcode == "LONG_DELAY") & (data!=0)): #done so dataField*delay = total delay length
            data = data - 1
            
        if (opcode == OPCODE.STOP) and (resync == 0):
            print("WARNING: Resync Flag set to 0 for STOP opcode. This may lead to an inconsistent starting phase across multiple runs of the program.")

       
        phasehop = 0 #TODO: Reimpliment once single cycle instructions works
        instrucNum = -1
        if(prepend == False):
            instrucNum = self.numInstructions
            instruction = MBInstruction(opcode,ttl,freq,phase,amp,delay,data,resync,phasehop,instrucNum,label)
            self.instructionList.append(instruction)
        elif(prepend == True):
            instrucNum = 0
            for instruc in self.instructionList:
                instruc.instructionNum +=1
                if(instruc.opcode in (OPCODE.END_LOOP, OPCODE.BRANCH, OPCODE.JSR)):
                    instruc.data = instruc.data + 1 #when an instruction is prepended,
            for key in self.labelDict.keys():
                self.labelDict[key] += 1 
            instruction = MBInstruction(opcode,ttl,freq,phase,amp,delay,data,resync,phasehop,instrucNum,label) #instruction num will be 0 if prepended
            self.instructionList.insert(0,instruction)
        else: 
            raise ValueError("Optional input arg prepend must be either true or false")
        
        if(label != None): #add the label to the instruction label dictionary, it's value is the instruction number
            if (label in self.labelDict.keys()):
                raise ValueError(f"Cannot give instruction {instrucNum} label {label} as it has already been assigned to another instruction")
            else:
                self.labelDict[label] = instrucNum        

        self.numInstructions += 1 
        return instruction.instructionNum

    def add_instruction(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, resync:bool = 0, prepend:bool = False, label: str = None) -> int:
        """Adds a instruction with the CONT (default) opcode

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        data = 0
        instrucNum = self.gen_instruction(OPCODE.CONT,ttl,freq,phase,amp,delay,data,resync,prepend,label)
        return instrucNum

    def end_program(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, resync:bool = 1, prepend:bool = False, label:str = None) -> int:
        """When executed, the DDS and output flags will be updated, then the program will halt and the MicroBlaster will return to the first instruction to await the start flag.

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        data = 0
        instrucNum = self.gen_instruction(OPCODE.STOP,ttl,freq,phase,amp,delay,data,resync,prepend,label)
        return instrucNum
    
    def start_loop(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, loops:int, resync:bool = 0, prepend:bool = False, label:str = None) -> int:
        """Begin a loop, each iteration of the loop will start from this instruction. 

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            loops (int): Number of times the loop should run
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        instrucNum = self.gen_instruction(OPCODE.LOOP,ttl,freq,phase,amp,delay,loops,resync,prepend,label)
        return instrucNum
    
    def end_loop(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, resync:bool = 0, prepend:bool = False, label:str = None) -> int:
        """Jumps back to the start of the currently running loop or continues to the next instruction ff the number of desired loops has been completed. 

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            return_addr (int): User may choose to manually enter the instruction number coresponding to the start_loop instruction of the current loop.
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        
        Raises:
            ReferenceError: Cannot find a start_loop instruction before end_loop instruction

        Returns:
            int: Position of the instruction in the instruction list.
        """
        return_addr = None
        loopCount = 0
        for i in range(self.numInstructions-1,-1,-1):
            match self.instructionList[i].opcode:
                case OPCODE.LOOP:
                    if loopCount == 0:
                        return_addr = i
                        break
                    else:
                        loopCount -= 1
                case OPCODE.END_LOOP:
                    loopCount += 1
                case _:
                    continue
        if(return_addr == None):
            raise ReferenceError("No start_loop instruction prior to end_loop instruction")
        instrucNum = self.gen_instruction(OPCODE.END_LOOP,ttl,freq,phase,amp,delay,return_addr,resync,prepend,label)
        return instrucNum
    
    def jump_subroutine(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, addr:str, resync:bool = 0, prepend:bool = False, label:str = None) -> int:
        """Jumps to the instruction with the given label

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            addr (str): String of the instruction label to jump to
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        instrucNum = self.gen_instruction(OPCODE.JSR,ttl,freq,phase,amp,delay,addr,resync,prepend,label)
        return instrucNum
    
    def return_subroutine(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, resync:bool = 0, prepend:bool = False, label:str = None) -> int:
        """Continues execution from the instruction after the previous jump_subroutine.

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        data = 0
        instrucNum = self.gen_instruction(OPCODE.RTS,ttl,freq,phase,amp,delay,data,resync,prepend,label)
        return instrucNum
    
    def branch(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, addr:str, resync:bool = 0, prepend:bool = False, label:str = None) -> int:
        """Jump to instruction given in the addr field

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            addt (str): Label of the instruction to jump to
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        instrucNum = self.gen_instruction(OPCODE.BRANCH,ttl,freq,phase,amp,delay,addr,resync,prepend,label)
        return instrucNum
    
    def long_delay(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, mult:int, resync:bool = 0, prepend:bool = False, label:str = None):
        """This instruction will run for mult*delay nanoseconds before continuing to the next instruction

        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Minimum value of 4, and must be an integer multiple of 2.
            mult (int): Multiplier that will be applied to the delay field to get the total delay in nanoseconds
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        instrucNum = self.gen_instruction(OPCODE.LONG_DELAY,ttl,freq,phase,amp,delay,mult,resync,prepend,label)
        return instrucNum
    
    def wait(self, ttl:int,  freq:float, phase:float, amp:int, delay:int, resync:bool = 0, prepend:bool = False, label:str = None):
        """Program execution will pause until the trigger line of the MicroBlaster goes high. After which it will wait for an additional [delay] nanoseconds before executing the next instruction
        Args:
            ttl (int): Each bit of this 12 bit number represents the state of one of the 12 output flags.  
            freq (float): Frequency of the output sine wave. Units in Hz
            phase (float): Relative phase offset of the output sine wave from 0. Units in degrees
            amp (int): Amplitude of the output sine wave. Values range from -32767 to 32767
            delay (int): Amount of time instruction will run for in nanoseconds before moving to the next instruction. Must be an integer multiple of 2.
            resync (bool, optional): When set high, the phase accumulator inside the DDS will be set to 0. Posedge triggered. Defaults to 0.
            prepend (bool, optional): When set to True, the instruction will be added to the start of the instruction list rather than the end. Defaults to False.
            label (str, optional): String used to reference this instruction in branch or jump_subroutine instructions. Defaults to None.

        Returns:
            int: Position of the instruction in the instruction list.
        """
        data = 0
        instrucNum = self.gen_instruction(OPCODE.WAIT,ttl,freq,phase,amp,delay,data,resync,prepend,label)
        return instrucNum
    
    def print_program(self):
        """Prints the current instruction list.
        """
        for i, entry in enumerate(self.instructionList):
            print(f"Instruction {entry.instructionNum}: opcode = {entry.opcode}, ttl = {entry.ttl}, freq = {entry.freq}Hz, phase = {entry.phase}deg, amp = {entry.amp}, delay = {entry.delay}ns, data = {entry.data}, resync = {entry.resync}, label = {entry.label}\n")
        
    def clean_program(self):
        """Removes all instructions from the instruction list.
        """
        self.dirty = True
        self.numInstructions = 0
        self.instructionList = []

    def save_program(self,filename: str):
        """Save program to a text file in the current working directory which can later be reloaded using load_program. Do not include file extention in filename
        
        Args:
            filename (str): Name of the file to save the program in. Do not include file extention in filename
        """
        fileHandle = open(filename+".pkl","wb")
        for instruc in self.instructionList:
            pickle.dump(instruc,fileHandle,pickle.HIGHEST_PROTOCOL)
        fileHandle.close()

    def load_program(self, filename: str) -> int:
        """Load a program from a of the name "filename", do not include file extention in filename. Runing this method will clear the current program

        Args:
            filename (str): The file that holds the program you wish to load. Do not include file extention in the filename.
        """
        self.clean_program()

        fileHandle = open(filename+".pkl","rb")
        numInstructions = 0
        while True:
            try:
                instruction = pickle.load(fileHandle)
                self.instructionList.append(instruction)
                numInstructions += 1
            except EOFError:
                break
        self.numInstructions = numInstructions
        return 0

    def get_freq_res(self) -> float:
        """
        Returns:
            int: Frequency resolution of the MicroBlaster in Hz
        """
        return MicroBlaster.freqRes

    def get_phase_res(self) -> float:
        """
        Returns:
            float: Phase resolution of the MicroBlaster in degrees
        """
        return MicroBlaster.phaseRes
    
    def get_max_amp(self) -> int:
        """

        Returns:
            int: Returns the absolute value of the maximum amplitude output 
        """
        return MicroBlaster.maxAmp
    
    def get_max_freq(self) -> float:
        """
        Returns:
            float: Returns the maximum frequency output in Hz. Setting the frequency to this value will cause it to hold the previous frequency value
        """
        return MicroBlaster.maxFreq
    
    def get_max_phase(self) -> float:
        """
        Returns:
            float: Returns the maximum phase offset in degrees
        """
        return MicroBlaster.maxPhase

    def update(self):
        bytes_array = bytearray()
        stopPresent = 0 #TODO: make sure this is still checked
        for instruction in self.instructionList:
            if(instruction.opcode == OPCODE.STOP):
                stopPresent = 1 
            bytes_array += instruction.encode_instruction(self.labelDict)
        if(stopPresent == 0):
            raise ValueError("MicroBlaster program must contain a stop command")
        return bytes_array, "api/pulseblaster"

    def __str__(self):
        output = ""
        output += f"[MicroBlaster] Number of Instructions = {self.numInstructions}\n"
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
            for i in range(int(MicroBlaster.instructionLength/32)): #this converts each instruction into 32 bit chunks
                flippedData = instr[::-1]
                scaledData = flippedData[i*32:(i+1)*32]
                scaledData = scaledData[::-1] #flip back
                dataFile.write(f"{scaledData}\n") #have to start from the end of the list since it is the lsb
                addressFile.write(f"{format(addrNum,f"0{awidth}b")}\n")
                addrNum += 4 #move 4 bytes over in memory

    def _generate_testbenchfile(self,filename):
        addressPointer=0
        workingDirectory = os.getcwd()
        opcode=self.instructionList[0][MicroBlaster.opcodeSB : MicroBlaster.opcodeSB+MicroBlaster.opcodeLen]   
        unwrappedFile = open(os.path.join(workingDirectory+filename),"w")
        unwrappedFile.write("1,1,0000000000000000,000000000000000000000000000000,000000000000000000000000000000,000000000000,0\n") #0 pad the start based on reset states
        loopStack = [[(2**self.addrBits)-1,0]] #first address is at the very end so when it is checked it always returns not used
        loopPointer = 0
        rtsAddress = 0
        counter = 0
        while (addressPointer < len(self.instructionList)):
            currentInstruction = self.instructionList[addressPointer]
            opcode = currentInstruction[MicroBlaster.opcodeSB : MicroBlaster.opcodeSB+MicroBlaster.opcodeLen]
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
            freqOutput = currentInstruction[self.freqSB : self.freqSB+self.freqLen] #account for downscaling from MicroBlaster
            ttlOutput = currentInstruction[self.ttlSB : self.ttlSB+self.ttlLen]
            #print(delayCounter)
            if(waitFlag == 0):
                for i in range((delayCounter+1)): #plus 1 because for a delay of 5 it should count from 0 up to 5 before wrapping around, divide by 2 since the input is ns not clock cycles
                    unwrappedFile.write(f"{phasehopFlag},{resyncFlag},{ampOutput},{phaseOutput},{freqOutput},{ttlOutput},{waitFlag}\n")
            else:
                unwrappedFile.write(f"{phasehopFlag},{resyncFlag},{ampOutput},{phaseOutput},{freqOutput},{ttlOutput},{waitFlag}\n")
        unwrappedFile.close()
