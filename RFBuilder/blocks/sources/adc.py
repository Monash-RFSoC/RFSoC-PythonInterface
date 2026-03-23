from ..base import Source
from ..port import Port, PortDirection

class ADC(Source):
    def __init__(self, tile: str, id: int):
        ports = [Port(PortDirection.OUTPUT, id)]
        super().__init__(tile, ports)

    def __str__(self):
        output = ""
        output += f"[ADC] Name: {self.name}\n"

        for port in self.ports:
            output += f"\t\t{str(port)}\n"

        return output

