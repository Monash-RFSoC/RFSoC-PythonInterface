from .boards import Board


class RFSOC4x2(Board):
    def __init__(self):
        super().__init__()

    def get_dacs(self):
        return ["dac_a", "dac_b"]

    def get_adcs(self):
        return ["adc_a", "adc_b", "adc_c", "adc_d"]

    def __str__(self) -> str:
        return "RFSoC4x2"