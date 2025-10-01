from RFBuilder.RFBlocks.Base import RFBlock, Port
from RFBuilder.RFBlocks.ProcessingNodes.ProcessingNode import ProcessingNode
from typing import List

from abc import ABC

class LowPassFilter(ProcessingNode):
    def __init__(self, fc: int) -> None:
        self.fc = fc
        ports = [Port(direction="input"), Port(direction="output")]
        super().__init__(ports)

    def to_dict(self) -> dict:
        _temp = super().to_dict()
        _temp["attributes"]["fc"] = self.fc

        return _temp