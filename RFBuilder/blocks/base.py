from abc import ABC, abstractmethod
from .port import Port

class RFBlock(ABC):
    def __init__(self, name: str, ports: list[Port]) -> None:
        self.name = name
        self.ports = ports
        self.attributes = {}
        self.dirty = True
        self.registered = False
        self.custom_update = False

    def to_dict(self):
        block = {
            "name" : self.name,
            "attributes" : self.attributes,
        }

        return block

    def get_ports(self) -> list[Port]:
        output_ports = []
        
        for port in self.ports:
            if port.available:
                output_ports.append(port)
                
                
        return output_ports
        
    def register_block(self, ip: str = "", port: int = 0):
        self.registered = True
        
    @abstractmethod
    def __str__(self):
        assert NotImplementedError


class Sink(RFBlock):
    def __init__(self, name: str, ports: list[Port]):
        # TODO: Check that all ports are inputs

        super().__init__(name, ports)
    pass


class Source(RFBlock):
    def __init__(self, name: str, ports: list[Port]):
        # TODO: Check that all ports are outputs
        
        super().__init__(name, ports)
    pass


class Processor(RFBlock):
    def __init__(self, name: str, ports: list[Port]):

        super().__init__(name, ports)