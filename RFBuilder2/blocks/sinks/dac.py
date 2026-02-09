from ..base import Source
from ..port import Port, PortDirection

class DAC(Source):
    def __init__(self, tile: str):
        ports = [Port(PortDirection.INPUT, 0)]
        super().__init__(tile, ports)

    def __str__(self):
        output = ""
        output += f"[DAC] Name: {self.name}\n"

        for port in self.ports:
            output += f"\t\t{str(port)}\n"
    
        return output