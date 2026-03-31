import tqdm

import RFBuilder
from RFBuilder.blocks.sources.pulse_blaster import PulseBlaster
from .rftester import Base

import numpy as np

class PBSimStep:
    def __init__(self, freq: int, phase: int, amplitude: int, duration: int, phasehop: int = 0, resync: int = 0, ttl: int = 0):
        self.freq = freq
        self.phase = phase
        self.amplitude = amplitude
        self.duration = duration
        self.phasehop = phasehop
        self.resync = resync
        self.ttl = ttl

class PBTester(Base):
    def __init__(self, rfbuilder: RFBuilder.RFBuilder, pb: RFBuilder.PulseBlaster):
        super().__init__(rfbuilder)
        self.pb = pb


    ## Test function, returns a time and data array.
    def test(self, type: str = "internal") -> tuple[np.ndarray, np.ndarray]:
        self.pb.prepend_instruction(0, 0, 0, 0, 500, 0, 0, "CONT", 10)
        self.pb.prepend_instruction(0, 0, 2**15-1, 0, 500, 0, 0, "CONT", 10)
        self.pb.prepend_instruction(0, 0, 0, 0, 500, 0, 0, "WAIT", 4)

        self.rf_builder.add(self.pb)

        logger = RFBuilder.DataLogger()
        self.rf_builder.add(logger)

        dacs = self.rf_builder.get_dacs()
        adcs = self.rf_builder.get_adcs()

        if type == "internal":
            self.rf_builder.connect(self.pb, logger)
        elif type == "feedback":
            self.rf_builder.connect(self.pb, dacs[0])
            self.rf_builder.connect(adcs[1], logger)

        self.rf_builder.ttl.reset()

        self.rf_builder.ttl.connect("SOFTWARE0", ["DIGITIZER_TRIG0", "PB_TRIG", "SYZYGY_OUT0"])
        self.rf_builder.ttl.connect("SOFTWARE1", "PB_RSTN")
        self.rf_builder.ttl.connect("SOFTWARE2", "PB_RUN")

        self.rf_builder.ttl.update_state("SOFTWARE1", 0)
        self.rf_builder.ttl.update_state("SOFTWARE1", 1)
        self.rf_builder.ttl.update_state("SOFTWARE2", 0)
        self.rf_builder.ttl.update_state("SOFTWARE0", 0)

        self.rf_builder.update()

        ## Pulse blaster has had a small 'wait' instruction prepended to it, so the users program should not be running yet.
        # will only test ~10 micro-seconds worth of pulses.
        
        ## Run the pulse blaster, it should stop at the test harness WAIT command
        self.rf_builder.ttl.update_state("SOFTWARE2", 1)

        ## Trigger the blaster and digitizer capture.
        self.rf_builder.ttl.update_state("SOFTWARE0", 2)

        ## Read 10.5 micro-seconds. 10 micro-seconds for the test, and 0.5 at the start for delays and other shenanigans.
        test_data, test_time = logger.read(num_seconds=1.5e-6)

        if type == "feedback":
            test_time *= 8/5

        og_data = test_data.copy()
        og_time = test_time.copy()

        print("Data logger read complete. Data:")

        ## Read statistics
        ## Number of "0" samples at the start, measures the delay between triggering and output
        delay_time, test_data, test_time = self.trim_zeros(test_data, test_time)
        print(f"\tFound trigger latency of {(delay_time - 4e-9) * 1e9:.2f} ns")

        ## Find the end of the pulse by looking for two consecutive "0" samples, measures the pulse duration
        duration, amplitude, frequency, test_data, test_time = self.trim_pulse(test_data, test_time)

        print(f"\n\tTest start pulse detected!!!")
        print(f"\tTrigger Pulse duration was {duration * 1e9:.2f} ns")
        print(f"\tTrigger Pulse frequency was {frequency:.2f} MHz\n")

        pulse_time, _, _ = self.trim_zeros(test_data, test_time)
        print(f"\tTrimmed tester start delay of {pulse_time * 1e9:.2f} ns")
        print(f"\tUser Pulse Blaster code starts at {(delay_time + pulse_time + duration) * 1e9:.2f} ns")

        ## At this point, test_data and test_time only contain the information from the start of the user program.
        pulseBlasterOutput = self.simulate()

        print("\nPulse blaster output from simulation:")
        for step in pulseBlasterOutput:
            print(f"\tFreq: {step.freq}, Phase: {step.phase}, Amplitude: {step.amplitude}, Duration: {step.duration}, PhaseHop: {step.phasehop}, Resync: {step.resync}, TTL: {step.ttl}")


        sim_data, sim_time = self.generate_waveform(pulseBlasterOutput, delay_time - 4e-9, 16e9)
        self.compare_waveforms(og_data, og_time, sim_data, sim_time)

        test_amp = np.max(test_data)
        sim_data = np.array(sim_data) * (test_amp / np.max(sim_data))

        return og_data, og_time, sim_data, sim_time, delay_time
    

    def compare_waveforms(self, test_data: np.ndarray, test_time: np.ndarray, sim_data: np.ndarray, sim_time: np.ndarray):
        ## Compare the simulated waveform to the actual data

        # Match the amplitude of the two waveforms
        test_amp = np.max(test_data)
        sim_data = np.array(sim_data) * (test_amp / np.max(sim_data))
        sim_data /= np.max(sim_data)
        test_data = np.array(test_data) / np.max(test_data)

        # find the comparison window
        sim_filtered = []
        for t in test_time:
            idx = np.argmin(np.abs(sim_time - t))
            sim_filtered.append(sim_data[idx])

        base_mse = np.mean((sim_filtered - test_data) ** 2)
        print("\n\nPerforming initial comparison:")
        print(f"  Base MSE: {base_mse}\n")

        min_mse = base_mse
        min_shift = 0
        print("Performing time-shifted comparisons:")
        for time_shift in tqdm.tqdm(np.arange(-10e-9, 10e-9, 500e-12)):
            # find the comparison window
            sim_filtered = []
            for t in test_time:
                idx = np.argmin(np.abs(sim_time - t - time_shift))
                sim_filtered.append(sim_data[idx])
                
            mse = np.mean((sim_filtered - test_data) ** 2)
            if mse < min_mse:
                min_mse = mse
                min_shift = time_shift

    
        print(f"  Best time shift: {min_shift * 1e9:.2f} ns, MSE: {min_mse}")



    
    def generate_waveform(self, sim_steps: list[PBSimStep], delay: float, fs: float = 8e9) -> tuple[np.ndarray, np.ndarray]:
        """Generates the expected pulse blaster waveform.

        Multiple sampling rates are available, because you may want to compare it with/without the quantisation of lower sampling rates.

        The waveform is constructed using the simulation output of the pulseblaster function. 


        Args:
            sim_steps (list[PBSimStep]): The list of simulations steps from the pulse blaster simulation. 
            delay (float): The initial delay before the start of the pulse blaster program, should be found by aligning the test pulse.
            fs (float): Sampling rate of the reconstructed waveform

        Returns:
            tuple[np.ndarray, np.ndarray]: waveform data and corresponding time arrays. Output[0] = data, Output[1] = time
        """
        time = []
        data = []

        phase_inc = 0

        current_time = delay + 1/fs
        fs /= 1e9 # Expecting GSa/s

        print("\nReconstructing Pulse Blaster waveform at a sample rate of {:.2f} GSa/s.".format(fs))
        for step in tqdm.tqdm(sim_steps):
            step.duration = step.duration * 1e-9 #convert from nano-seconds to seconds
            step.amplitude /= 2
            num_samples = int(step.duration / (1e-9 / fs)) #convert duration from nano-seconds to number of samples at 8 GSPS
            t = np.linspace(current_time, current_time + step.duration, num_samples, endpoint=False)
            for _ in range(num_samples):
                phase_inc += (2 * np.pi * step.freq) * (1e-9 / fs) #increment phase based on frequency and sample rate
                waveform = step.amplitude * np.sin(phase_inc)
                data.append(waveform)

            time.append(t)
            current_time += step.duration
        
        return data, np.concatenate(time)
    
    # Returns a list of steps, each step is represented by a PBSimStep Object
    def simulate(self) -> list[PBSimStep]:
        ## Simulate the pulse blaster program

        outputWaveform = [] # PBSimStep Objects

        addressPointer=0

        loopStack = [[(2**self.pb._addrBits)-1,0]] #first address is at the very end so when it is checked it always returns not used
        loopPointer = 0
        
        rtsAddress = 0
        
        while (addressPointer < len(self.pb.instruction_list)):
            currentInstruction = self.pb.instruction_list[addressPointer]
            opcode = currentInstruction[PulseBlaster._opcodeSB : PulseBlaster._opcodeSB+PulseBlaster._opcodeLen]
            opcode = int(opcode,2)
            delayCounter = int(currentInstruction[self.pb._delaySB : self.pb._delaySB+self.pb._delayLen],2)

            if(opcode == self.pb._opcodeDict["CONT"]):
                addressPointer += 1
            elif (opcode == self.pb._opcodeDict["STOP"]):
                addressPointer = len(self.pb.instruction_list)
            elif (opcode == self.pb._opcodeDict["LOOP"]):
                if(addressPointer != loopStack[loopPointer][0]):
                    if(loopStack[loopPointer][0] == 2**self.pb._addrBits-1):
                        loopStack[loopPointer][0] = addressPointer
                        loopStack[loopPointer][1] = int(currentInstruction[self.pb._dataSB : self.pb._dataSB+self.pb._dataLen],2)
                    else:
                        loopPointer += 1
                        loopStack.append([addressPointer,int(currentInstruction[self.pb._dataSB : self.pb._dataSB+self.pb._dataLen],2)])
                addressPointer += 1
            elif (opcode == self.pb._opcodeDict["END_LOOP"]):
                loopStack[loopPointer][1] -= 1
                if(loopStack[loopPointer][1] == 0):
                    addressPointer +=1
                    if(len(loopStack)>1):
                        loopStack.pop(-1) #remove that entry from the loopStack
                        loopPointer -= 1
                    else:
                        loopStack = [[2**self.pb._addrBits-1,0]]
                        loopPointer = 0
                else:
                    addressPointer = int(currentInstruction[self.pb._dataSB : self.pb._dataSB+self.pb._dataLen],2) #should have the loop address in the data field
            elif (opcode == self.pb._opcodeDict["JSR"]):
                rtsAddress = addressPointer+1
                addressPointer = int(currentInstruction[self.pb._dataSB : self.pb._dataSB+self.pb._dataLen],2) #should have the subroutine address in the data field
            elif (opcode == self.pb._opcodeDict["RTS"]):
                addressPointer = rtsAddress
            elif (opcode == self.pb._opcodeDict["BRANCH"]):
                addressPointer = int(currentInstruction[self.pb._dataSB : self.pb._dataSB+self.pb._dataLen],2) #should have the branch address in the data field
            elif (opcode == self.pb._opcodeDict["LONG_DELAY"]):
                addressPointer += 1 #here there is just a longer delay which the tb currently doesn't check since it is an internal param
                delayCounter = delayCounter * int(currentInstruction[self.pb._dataSB : self.pb._dataSB+self.pb._dataLen],2)
            elif (opcode == self.pb._opcodeDict["WAIT"]):
                addressPointer += 1 #since this is just getting the expected output of the instructions no need to do anything apart from incriment counter
            else:
                raise ValueError(f"The instruction at address {addressPointer} does not contain a valid opcode: {opcode}")

            ampOutput = currentInstruction[self.pb._ampSB : self.pb._ampSB+self.pb._ampLen]
            resyncFlag = currentInstruction[self.pb._resyncSB : self.pb._resyncSB+self.pb._resyncLen]
            phasehopFlag = currentInstruction[self.pb._phasehopSB : self.pb._phasehopSB+self.pb._phasehopLen]
            phaseOutput = currentInstruction[self.pb._phaseSB : self.pb._phaseSB+self.pb._phaseLen]
            freqOutput = self.fetch_mask(currentInstruction, self.pb._freqSB, self.pb._freqLen) #account for downscaling from PulseBlaster
            ttlOutput = currentInstruction[self.pb._ttlSB : self.pb._ttlSB+self.pb._ttlLen]

            freq_scalar = 4_000_000_000 / (1 << 31)

            sim_step = PBSimStep(np.ceil(freqOutput * freq_scalar), int(phaseOutput, 2), int(ampOutput, 2), delayCounter * 2 + 2, int(phasehopFlag, 2), int(resyncFlag, 2), int(ttlOutput, 2))
            outputWaveform.append(sim_step)
                
                
        
        return outputWaveform

    def fetch_mask(self, val, offset, width):
        return int(val[offset:offset+width], 2)