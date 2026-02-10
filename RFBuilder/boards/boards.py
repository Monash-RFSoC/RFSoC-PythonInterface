from abc import ABC, abstractmethod


class Board(ABC):
    @abstractmethod
    def __init__(self):
        assert NotImplementedError

    @abstractmethod
    def get_dacs(self):
        assert NotImplementedError

    @abstractmethod
    def get_adcs(self):
        assert NotImplementedError

    @abstractmethod
    def __str__(self):
        assert NotImplementedError


