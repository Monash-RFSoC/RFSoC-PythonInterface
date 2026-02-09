from platform import system
from .RFBlocks.Base import RFBlock, Port

class RFBuilder():
    def __init__(self):
        self.blocks = []

    def add_block(self, block: RFBlock) -> int:
        if not hasattr(block, 'to_dict'):
            raise ValueError("Block must have a to_dict method.")
        
        if not isinstance(block, RFBlock):
            raise TypeError("Block must be an instance of RFBlock or its subclasses.")

        block.id = str(len(self.blocks) + 1)

        self.blocks.append(block)
        return block.id

    def add_connection(self, source: int, sink: int):
        source_block = next((block for block in self.blocks if block.id == source), None)
        if source_block is None:
            raise ValueError(f"Source block with id {source} not found.")
        
        sink_block = next((block for block in self.blocks if block.id == sink), None)
        if sink_block is None:
            raise ValueError(f"Sink block with id {sink} not found.")
        
        source_port = next((port for port in source_block.ports if (port.direction == "output" and port.connection == None)), None)
        if source_port is None:
            raise ValueError(f"No available output port found in source block with id {source}.")
        
        sink_port = next((port for port in sink_block.ports if (port.direction == "input" and port.connection == None)), None)
        if sink_port is None:
            raise ValueError(f"No available input port found in sink block with id {sink}.")
        
        source_port.connect(sink_port)

    def construct_packet(self) -> dict:
        data = {
            "request-type": "build-system",
            "system": self.to_dict()
        }
        return data

    def to_dict(self):
        _dict = {
            "blocks": [block.to_dict() for block in self.blocks],
        }

        return _dict

    def __str__(self):
        _str = "----- RFBuilder System Overview -----\n"
        _str += f"    Number of blocks: {len(self.blocks)}\n"
        _str += "-------------------------------------\n"
        for block in self.blocks:
            _str += str(block)
            _str += "\n    ---\n"

        _str += "\n\n    ---\n"

        return _str