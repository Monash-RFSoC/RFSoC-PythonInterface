from abc import ABC, abstractmethod

from RFBuilder.control import ControlManager, ControlPin
from .port import Port
from ..networking import send_http_data

class RFBlock(ABC):
    def __init__(self, name: str, ports: list[Port]) -> None:
        self.name = name
        self.ports = ports
        self.attributes = {}
        self.dirty = True
        self.registered = False
        self.custom_update = False
        self.ip = None
        self.port = None
        self.pins = []

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
    
    def ttl(self) -> list[ControlPin]:
        return self.pins

    
    def register_block(self, ip: str = "", port: int = 0, index: int = 0, ttl: ControlManager = None):
        self.registered = True
        #self.ip = ip
        #self.port = port
        
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