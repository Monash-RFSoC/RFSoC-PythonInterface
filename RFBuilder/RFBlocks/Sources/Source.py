from RFBuilder.RFBlocks.Base import RFBlock, Port
from typing import List

class Source(RFBlock):
    def __init__(self, ports: List[Port]):
        if not all(port.direction == "output" for port in ports):
            raise ValueError("All ports in a Source must be output ports.")
        
        super().__init__(ports)