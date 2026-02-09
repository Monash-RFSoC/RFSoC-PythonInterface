from RFBuilder.RFBlocks.Base import RFBlock, Port
from typing import List

class Sink(RFBlock):
    def __init__(self, ports: List[Port]):
        if not all(port.direction == "input" for port in ports):
            raise ValueError("All ports in a Sink must be input ports.")

        super().__init__(ports)