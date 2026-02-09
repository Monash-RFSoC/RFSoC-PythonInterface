from abc import ABC
from .boards.boards import Board
from .blocks.base import RFBlock
from .blocks.sinks.dac import DAC
from .blocks.sources.adc import ADC


class RFBuilder(ABC):
    def __init__(self, board: Board):
        self.board = board
        self.blocks = []
        
        # Register all available DACs
        for dac in self.board.get_dacs():
            block = DAC(dac)
            self.register_block(block)

        for adc in self.board.get_adcs():
            block = ADC(adc)
            self.register_block(block)


    def register_block(self, block: RFBlock):
        for i in self.blocks:
            if i.name == block.name:
                raise KeyError("Attempted to add duplicate block to system")

        self.blocks.append(block)

    def export(self):
        # Export the RFBuilder system to JSON for the RFSoC to process.
        system = {}

        system["blocks"] = [block.to_dict() for block in self.blocks]
    
        return system 




    def __str__(self):
        output = ""
        output += "┌─────────────────────────────────┐\n"
        output += "│        RFBuilder Layout         │\n"
        output += "└─────────────────────────────────┘\n\n"
        output += f"\tBoard : {str(self.board)}\n"

        # print the RF capabilities of the board
        output += f"\tDACs : {self.board.get_dacs()}\n"
        output += f"\tADCs : {self.board.get_adcs()}\n"

        output += "\n──────────────────────────────────────────────────────────────────\n\n"
        
        for block in self.blocks:
            output += f"\t{str(block)}"

        return output
