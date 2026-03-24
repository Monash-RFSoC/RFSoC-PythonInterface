from ..base import Processor
from ..port import Port, PortDirection

class Mixer(Processor):
    def __init__(self):
        ports = [
            Port(PortDirection.INPUT, 2),
            Port(PortDirection.INPUT, 3),
            Port(PortDirection.OUTPUT, 3)
        ]

        super().__init__("mixer", ports)
    
    def __str__(self):
        output = ""

        output += f"\t[Mixer]\n"
        
        return output