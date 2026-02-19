from abc import ABC
from enum import Enum

class IODirection(Enum):
    INPUT = 0
    OUTPUT = 1
    INOUT = 2

class IO(ABC):
    def __init__(self, direction: IODirection, endpoint: str):
        self.direction = direction
        self.endpoint = endpoint
        

    

        
        


    def __str__(self):
        return f"[IO] ID : {self.id} | Direction : {self.direction} | Available : {self.available}"