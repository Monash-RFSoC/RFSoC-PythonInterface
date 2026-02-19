from abc import ABC, abstractmethod
from .port import Port
from .io import IO

class RFBlock(ABC):
    def __init__(self, name: str, ports: list[Port], ios: dict[str, IO]) -> None:
        self.name = name
        self.ports = ports
        self.ios = ios
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
    
    def get_ios(self) -> dict[str, IO]:
        return self.ios
        
    def register_block(self):
        self.registered = True
        
    @abstractmethod
    def __str__(self):
        assert NotImplementedError


class Sink(RFBlock):
    def __init__(self, name: str, ports: list[Port], ios: list[IO]):
        # TODO: Check that all ports are inputs

        super().__init__(name, ports, ios)
    pass


class Source(RFBlock):
    def __init__(self, name: str, ports: list[Port], ios: list[IO]):
        # TODO: Check that all ports are outputs
        
        super().__init__(name, ports, ios)
    pass



