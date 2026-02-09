from .Sink import Sink
from RFBuilder.RFBlocks.Base import Port

class DAC(Sink):
    def __init__(self) -> None:
        port = Port(direction="input")
        super().__init__([port])

    def to_dict(self) -> dict:
        _temp = super().to_dict()
        return _temp