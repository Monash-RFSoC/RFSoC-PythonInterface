from .Source import Source
from RFBuilder.RFBlocks.Base import Port

class MemSource(Source):
    def __init__(self, base_address, stream_length) -> None:
        port = Port(direction="output")
        super().__init__([port])
        self.base_address = base_address
        self.stream_length = stream_length

    def to_dict(self) -> dict:
        _temp = super().to_dict()
        _temp.update({
            "base_address": self.base_address,
            "stream_length": self.stream_length
        })
        return _temp