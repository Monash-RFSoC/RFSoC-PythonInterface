from .boards.boards import Board

from abc import ABC
class ControlPin(ABC):
    INPUT = 0
    OUTPUT = 1

    def __init__(self, name: str, id: int, direction: int, software_controlled: bool = False):
        self.name = name
        self.id = id
        self.direction = direction
        self.software_controlled = software_controlled


    def __str__(self):
        return f"{self.name} (ID: {self.id}, Direction: {'INPUT' if self.direction == ControlPin.INPUT else 'OUTPUT'})"

class PinDict(dict):
    def __getattr__(self, name):
        return self[name]
    
class PinConnection(list):
    def __str__(self):
        if not self:
            return "No connections."
        
        source = self[0]  
        sink = self[1]

        output = ""

        output += f"{source.name} --> {sink.name}\n"
        
        return output
    

class PinConnections(list):
    def __init__(self, operations: list[tuple[ControlPin, int]]):
        super().__init__()
        self.operations = operations

    def __str__(self):
        from collections import defaultdict
        if not self:
            return "No connections."

        sink_to_sources = defaultdict(list)
        for source, sink in self:
            sink_to_sources[sink].append(source)

        # Find longest input name for alignment
        max_len = max(len(source.name) for source, sink in self)

        output = "Control Pin Connections (Tree View):\n\n"
        for sink, sources in sink_to_sources.items():
            for i, source in enumerate(sources):
                is_last = i == len(sources) - 1
                is_first = i == 0

                if len(sources) == 1:
                    branch = "━━"
                elif is_first:
                    branch = "┳━"
                elif is_last:
                    branch = "┛"
                else:
                    branch = "┫"

                opString = "[ AND ]" if (sink, 1) in self.operations else "[ OR  ]" if (sink, 0) in self.operations else "[ OR  ]"
                if len(sources) == 1:
                    opString = "━━━━━━━"
                sink_label = f"{opString}━━ {sink.name}" if is_first else ""
                padded_name = f"{source.name}".ljust(max_len )
                output += f"  {padded_name} ━━{branch}{sink_label}\n"

            output += "\n"
        return output


class ControlManager(ABC):
    def __init__(self, board: Board, rfbuilder):
        self.board = board
        self.pins: PinDict[str, list[ControlPin]] = self.board.get_ttl_pins()
        self.operations: list[tuple[ControlPin, int]] = []
        self.connections: PinConnections = PinConnections(self.operations)
        self.dirty = False
        self.aliases = {}
        self.rfbuilder = rfbuilder

    def add_alias(self, alias: str, pin: ControlPin | list[ControlPin] | str | list[str]):
        if isinstance(pin, str):
            pin = self.get_pin(pin)

        if isinstance(pin, list):
            for idx, p in enumerate(pin):
                if isinstance(p, str):
                    pin[idx] = self.get_pin(p)
                elif not isinstance(p, ControlPin):
                    raise TypeError("All items in pin list must be ControlPin instances or valid pin names.")


        if alias in self.aliases:
            raise KeyError(f"Alias {alias} already exists.")
                

        self.aliases[alias] = pin

    def connect(self, source_pin: ControlPin | list[ControlPin] | str | list[str], sink_pin: ControlPin | list[ControlPin] | str | list[str]):
        if isinstance(source_pin, str):
            source_pin = self.get_pin(source_pin)

        if isinstance(sink_pin, str):
            sink_pin = self.get_pin(sink_pin)

        if not (isinstance(source_pin, ControlPin) or isinstance(source_pin, list)):
            raise TypeError("Source pin must be a ControlPin or list of of Control Pins. Maybe you meant to connect blocks with register_connection()?")

        if not (isinstance(sink_pin, ControlPin) or isinstance(sink_pin, list)):
            raise TypeError("Sink pin must be a ControlPin or list of Control Pins. Maybe you meant to connect blocks with register_connection()?")
                
                
        if isinstance(source_pin, list):
            for pin in source_pin:
                self.connect(pin, sink_pin)

            return
                
        if isinstance(sink_pin, list):
            for pin in sink_pin:
                self.connect(source_pin, pin)

            return

        if source_pin.direction != ControlPin.INPUT:
            raise ValueError(f"Source pin {source_pin} is not an input pin.")
        
        if sink_pin.direction != ControlPin.OUTPUT:
            raise ValueError(f"Sink pin {sink_pin} is not an output pin.")
        
        for connection in self.connections:
            if connection[0] == source_pin and connection[1] == sink_pin:
                raise ValueError(f"Pins {source_pin} and {sink_pin} are already connected.")
        
        self.dirty = True
        self.connections.append(PinConnection([source_pin, sink_pin]))

    def disconnect(self, source_pin: ControlPin, sink_pin: ControlPin):
        if (source_pin.direction != ControlPin.INPUT):
            raise ValueError(f"Source pin {source_pin} is not an input pin.")
        
        if (sink_pin.direction != ControlPin.OUTPUT):
            raise ValueError(f"Sink pin {sink_pin} is not an output pin.")
        
        if (source_pin, sink_pin) not in self.connections:
            raise ValueError(f"Pins {source_pin} and {sink_pin} are not connected.")
        
        self.dirty = True
        self.connections.remove((source_pin, sink_pin))

    def reset(self):
        self.dirty = True
        self.operations: list[tuple[ControlPin, int]] = []
        self.connections: PinConnections = PinConnections(self.operations)
        self.aliases = {}

    def update_state(self, pin: ControlPin | str, state: 0 | 1 | 2):
        if isinstance(pin, str):
            pin = self.get_pin(pin)

        if pin.software_controlled == False:
            raise ValueError(f"Pin {pin} is not software controlled and cannot have its state updated.")
        
        packet = (pin.id << 2) | (state & 0x3) ## STATE - 0: OFF, 1: ON, 2: PULSE
        packet = packet.to_bytes(1)

        self.rfbuilder.transmit_to_board(packet, "api/control")

    def set_operation(self, pin: ControlPin | str, operation: str):
        if isinstance(pin, str):
            pin = self.get_pin(pin)

        if operation not in ["AND", "OR"]:
            raise ValueError("Operation must be 'AND' or 'OR'.")
        
        if pin.direction != ControlPin.OUTPUT:
            raise ValueError(f"Pin {pin} is not an output pin and cannot have an operation.")
        
        self.operations.append((pin, 1 if operation == "AND" else 0))

    def get_pin(self, name: str) -> ControlPin:
        if name in self.aliases:
            return self.aliases[name]
        
        for key in self.pins:
            if isinstance(self.pins[key], list):
                for pin in self.pins[key]:
                    if pin.name == name:
                        return pin

            else:
                for subkey in self.pins[key]:
                    for pin in self.pins[key][subkey]:
                        if pin.name == name:
                            return pin
        
        raise KeyError(f"Pin with name {name} not found.")

    def __str__(self):
        output = ""
        for key in self.pins:
            if isinstance(self.pins[key], list):
                output += f"{key}:\n"
                for pin in self.pins[key]:
                    output += f"  - {pin}\n"

            else:
                output += f"{key}:\n"
                for subkey in self.pins[key]:
                    output += f"  {subkey}:\n"
                    for pin in self.pins[key][subkey]:
                        output += f"    - {pin}\n"
        
        return output