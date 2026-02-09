from abc import ABC, abstractmethod
from .port import Port

class RFBlock(ABC):
    def __init__(self, name: str, ports: list[Port]) -> None:
        self.name = name
        self.ports = ports
        self.attributes = {}

    def to_dict(self):
        block = {
            "name" : self.name,
            "attributes" : self.attributes,
            "ports" : [port.to_dict() for port in self.ports]
        }

        return block


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



