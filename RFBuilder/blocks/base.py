from abc import ABC, abstractmethod
from .port import Port
from ..networking import send_http_data
HIGH = 0x03
LOW = 0x02
PULSE = 0x01

class RFBlock(ABC):
    def __init__(self, name: str, ports: list[Port], pins: dict[str:int]) -> None:
        self.name = name
        self.ports = ports
        self.attributes = {}
        self.dirty = True
        self.registered = False
        self.custom_update = False
        self.ip = None
        self.port = None
        self.pins = pins

    def to_dict(self):
        block = {
            "name" : self.name,
            "attributes" : self.attributes,
        }

        return block

    def get_ports(self) -> list[Port]:
        output_ports = []
        
        for port in self.ports:
            if port.available:
                output_ports.append(port)

        return output_ports
    
    def get_pins(self) -> dict:
        print("Values assosiated with key indicate current pin state")
        print(self.pins)
        return self.pins
        
    def set_pin(self, pin: str, state: int) -> int:
        if(pin not in self.pins.keys()):
            print(f"Could not find {pin} in pin list for this ip block")
            return ValueError
        endpoint = "api/"+self.name+"/"+pin
        
        if(state == 0):
            send_http_data(endpoint, bytearray([LOW]), self.ip, self.port)
            self.pins.pin = 0
        else:
            send_http_data(bytearray([HIGH]), endpoint, self.ip, self.port)
            self.pins.pin = 1

        return 0 #TODO: have it return weather or not the request was sucsessful
    
    def pulse_pin(self, pin) -> int:
        if(pin not in self.pins.keys()):
            print(f"Could not find {pin} in pin list for this ip block")
            return ValueError
        endpoint = "api/"+self.name+"/"+pin
        send_http_data(bytearray([PULSE]), endpoint, self.ip, self.port)
        
        return 0 #TODO: have it return weather or not the request was sucsessful
        
    
    def register_block(self, ip: str = "", port: int = 0):
        self.registered = True
        #self.ip = ip
        #self.port = port
        
    @abstractmethod
    def __str__(self):
        assert NotImplementedError


class Sink(RFBlock):
    def __init__(self, name: str, ports: list[Port], pins: dict):
        # TODO: Check that all ports are inputs

        super().__init__(name, ports, pins)
    pass


class Source(RFBlock):
    def __init__(self, name: str, ports: list[Port], pins: dict):
        # TODO: Check that all ports are outputs
        
        super().__init__(name, ports, pins)
    pass


class Processor(RFBlock):
    def __init__(self, name: str, ports: list[Port], pins: dict):

        super().__init__(name, ports, pins)