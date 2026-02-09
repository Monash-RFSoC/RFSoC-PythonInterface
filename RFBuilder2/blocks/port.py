from abc import ABC
from enum import Enum

class PortDirection(Enum):
    INPUT = 0
    OUTPUT = 1

class Port(ABC):
    def __init__(self, direction: PortDirection, id: int):
        self.direction = direction
        self.id = id
        self.available = True

    def register_connection(self):
        if not self.available:
            raise OverflowError("Port already has a connection")
        
        self.available = False
        
        


    def __str__(self):
        return f"[Port] ID : {self.id} | Direction : {self.direction} | Available : {self.available}"