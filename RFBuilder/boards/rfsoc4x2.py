from .boards import Board


class RFSOC4x2(Board):
    def __init__(self):
        super().__init__()

    def get_dacs(self):
        return [{"name" : "dac_a", "id" : 1}, {"name" : "dac_b", "id" : 0}]

    def get_adcs(self):
        return [{"name" : "adc_b", "id" : 1}]

    def __str__(self) -> str:
        return "RFSoC4x2"
