

from RFBuilder.RFBlocks.Base.Port import Port
from RFBuilder.RFBlocks.Sources.Source import Source


class ArbitraryWaveformGenerator(Source):
    block_type = "ddr4"

    def __init__(self):
        ports = [Port("output")]

        super().__init__(ports=ports)


    def get_attributes(self) -> dict:
        return {
            
        }
