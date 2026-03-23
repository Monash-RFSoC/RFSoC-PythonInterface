from abc import ABC
from enum import Enum

from RFBuilder.control import ControlManager, ControlPin
from .boards.boards import Board
from .blocks.base import RFBlock
from .blocks.sinks.dac import DAC
from .blocks.sources.adc import ADC

from .networking import send_http_data

class Clock_Config(Enum):
    Ext_Ref = "ext_ref"
    Int_Ref = "int_ref"

class RFBuilder(ABC):
    def __init__(self, board: Board, ip: str, port: int):
        # RFBuilder information
        self.board = board
        self.blocks : list[RFBlock] = [] 
        self.connections : list[tuple[int, int]] = []
        self.connections_dirty : bool = False
        
        # RFBuilder Networking Information
        self.ip = ip
        self.port = port

        # TTL Control pin setup
        self.ttl = ControlManager(self.board, self)
        
        # Register all available DACs
        for dac in self.board.get_dacs():
            block = DAC(dac["name"], dac["id"])
            self.register_block(block)

        for adc in self.board.get_adcs():
            block = ADC(adc["name"], adc["id"])
            self.register_block(block)


    def register_block(self, block: RFBlock):
        ## TODO: Add a dictionary to each board file that specifies how many of each block are available.

        same_blocks = [b for b in self.blocks if block.name in b.name]

        self.blocks.append(block)
        block.register_block(self.ip, self.port, len(same_blocks), self.ttl)

    def register_connection(self, source_block: RFBlock, sink_block: RFBlock):
        if not source_block.registered:
            raise ModuleNotFoundError(f"The {source_block} module has not been registered with an RFBuilder system.")
        
        if not sink_block.registered:
            raise ModuleNotFoundError(f"The {sink_block} module has not been registered with an RFBuilder system.")
        
        source_port = source_block.get_ports()[0]
        sink_port = sink_block.get_ports()[0]
        
        if not source_port:
            raise ConnectionError(f"{source_block} does not have an available output port.")
            
        # print(sink_port)
        if not sink_port:
            raise ConnectionError(f"{sink_block} does not have an available input port.")

        source_port.register_connection()
        sink_port.register_connection()
        
        self.connections.append([source_port.id, sink_port.id])
        self.connections_dirty = True

    def update(self):
        # Export the RFBuilder system to JSON for the RFSoC to process.
        system = {
            "blocks": []
        }

        update_queue = []

        for block in self.blocks:
            if block.dirty:
                block.dirty = False
                system["blocks"].append(block.to_dict())
                if block.custom_update:
                    update_queue.append(block)
                
        if self.connections_dirty:
            system["connections"] = self.connections

        if self.ttl.dirty:
            self.ttl.dirty = False
            connection_packet = []
            operations_packet = []

            for connection in self.ttl.connections:
                connection_packet.append([connection[0].id, connection[1].id])

            for operation in self.ttl.operations:
                operations_packet.append([operation[0].id, operation[1]])

            system["ttl"] = {
                "connections": connection_packet,
                "operations": operations_packet
            }

        if (system != {"blocks": []}):
            ## If there are updates to send, construct the data object to send
            request = {
                "request-type" : "build_system",
                "system" : system
            }

            # Default system update
            self.transmit_to_board(request, "api/system")

        else:
            ## No system updates to send, jump to custom updates
            pass

        # Custom updates for blocks that require it
        for block in update_queue:
            data, endpoint = block.update()
            self.transmit_to_board(data, endpoint)

        return system
    
    def transmit_to_board(self, data: dict, endpoint: str):
        ## TODO: Probably some checks on the data or something :/
        send_http_data(data, endpoint, self.ip, self.port)
    
    def configure_clock(self, ref: Clock_Config):
        if ref == Clock_Config.Ext_Ref:
            pass
        elif ref == Clock_Config.Int_Ref:
            pass
        else:
            raise ValueError("Unkown Clock Reference provided, must be either Ext_Ref or Int_Ref")
    
    def get_dacs(self):
        dacs = []
        
        for block in self.blocks:
            if "dac" in block.name:
                dacs.append(block)

        return dacs

    def get_adcs(self):
        adcs = []
        
        for block in self.blocks:
            if "adc" in block.name:
                adcs.append(block)
                
                
        return adcs

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

        output += "\n──────────────────────────────────────────────────────────────────\n\n"
        
        output += self.ttl.connections.__str__()
        
        return output
