from ..base import Source
from ..port import Port, PortDirection

import numpy as np

from enum import Enum

class WaveType(Enum):
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"


class ArbitraryDataGenerator(Source):
    def __init__(self, data: list):
        self.waveform: list = data
        
        super().__init__("ddr4", [Port(PortDirection.OUTPUT, 0)])
    
        self.custom_update = True

    def set_freq(self, freq: float):
        self.freq = freq
        self.dirty = True

    def set_wave_type(self, wave_type: WaveType):
        self.wave_type = wave_type
        self.dirty = True
        
    def generate_waveform(self):
        return self.waveform, len(self.waveform) * 2  # Each sample is 2 bytes (int16)
        

    def update(self):
        wave_data, num_bytes = self.generate_waveform()
        
        bytes_array = bytearray()
        for sample in wave_data:
            bytes_array += sample.to_bytes(2, byteorder='little', signed=True)

        return bytes_array, "api/stream"

        
    def to_dict(self):
        wave_data, num_bytes = self.generate_waveform()
        
        self.attributes = {
            "waveform" : [],
            "stream_length" : num_bytes,
            "base_address" : 0x0
        }
        
        return super().to_dict()
    
    def __str__(self):
        output = ""
        output += f"[ADG] Num Samples = {len(self.waveform)}\n"
        for port in self.ports:
            output += f"\t\t{str(port)}\n"

        
        return output
    
    
    
    