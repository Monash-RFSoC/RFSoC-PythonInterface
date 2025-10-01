from .Source import Source
from RFBuilder.RFBlocks.Base import Port
from enum import Enum

class WaveType(Enum):
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    PWM = "pwm"
    NOISE = "noise"


class WaveGenerator(Source):
    def __init__(self, freq: int, wave_type: WaveType) -> None:
        port = Port(direction="output")
        self.freq = freq
        self.wave_type = wave_type
        super().__init__([port])

    def to_dict(self) -> dict:
        _temp = super().to_dict()
        _temp['freq'] = self.freq
        _temp['wave_type'] = self.wave_type.value
        return _temp
