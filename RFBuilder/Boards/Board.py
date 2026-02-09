

from abc import ABC


class Board(ABC):
    def __init__(self):
        self.blocks = []