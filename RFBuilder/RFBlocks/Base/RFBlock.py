from .Port import Port
from typing import List

from abc import ABC, abstractmethod

class RFBlock(ABC):
    def __init__ (self, ports: List[Port]):
        self.id = None
        self.ports = ports

    @property
    @abstractmethod
    def block_type(cls):
        pass

    @abstractmethod
    def get_attributes(self) -> dict:
        pass

    def to_dict(self) -> dict:
        return {
            "type": self.block_type,
            "id": self.id,
            "ports": [port.to_dict() for port in self.ports],
            "attributes": self.get_attributes()
        }
    
    def __str__(self):
        _dict = self.to_dict()
        _str = f"    Block Type: {_dict["type"]}\n"
        _str += f"    Block ID: {_dict["id"]}\n"
        _str += f"    Ports: {_dict["ports"]}\n"

        for attr in _dict["attributes"].keys():
            _str += f"    {attr}: {_dict["attributes"][attr]}"


        return _str