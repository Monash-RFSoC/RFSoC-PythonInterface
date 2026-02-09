from abc import ABC
from enum import Enum

class PortDirection(Enum):
    INPUT = 0
    OUTPUT = 1

class Port(ABC):
    def __init__(self, direction: PortDirection, id: int):
        self.direction = direction
        self.id = id
        self.connection = {}

    def register_connect(self, name: str, id: int):
        self.connection = {
            "name"  :   name,
            "id"    :   id
        }

    def to_dict(self):
        return {
            "id"        : self.id,
            "direction" : self.direction.value,
            "connection": self.connection
        }

    def __str__(self):
        return f"[Port] ID : {self.id} | Direction : {self.direction}"