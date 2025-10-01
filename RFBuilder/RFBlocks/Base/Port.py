from __future__ import annotations
from typing import Literal

NodeDirection = Literal["input", "output"]


class Port():
    def __init__ (self, direction: NodeDirection) -> None:
        self.direction = direction
        self.connection = None

    def set_id(self, id: str):
        self.id = id
        
    def check_compatability(self, other_port: Port) -> bool:
        if (self.direction == other_port.direction):
            return False
        
        return True
    
    def connect(self, other_port: Port) -> None:
        if not self.check_compatability(other_port):
            raise ValueError("Ports are not compatible for connection.")
        
        self.connection = other_port
        other_port.connection = self

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "connection": self.connection.id if self.connection else {}
        }