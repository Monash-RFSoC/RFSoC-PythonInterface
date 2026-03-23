from ..base import Sink
from ..port import Port, PortDirection

class DAC(Sink):
    def __init__(self, tile: str, id: int):
        ports = [Port(PortDirection.INPUT, id)]
        super().__init__(tile, ports)

    def __str__(self):
        output = ""
        output += f"[DAC] Name: {self.name}\n"

        for port in self.ports:
            output += f"\t\t{str(port)}\n"
    
        return output