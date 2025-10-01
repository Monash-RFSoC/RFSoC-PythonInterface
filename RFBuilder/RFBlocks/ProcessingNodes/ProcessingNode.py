from RFBuilder.RFBlocks.Base import RFBlock, Port
from typing import List

from abc import ABC

class ProcessingNode(RFBlock, ABC):
    def __init__(self, ports: List[Port]) -> None:       
        super().__init__(ports)
