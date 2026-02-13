from ..base import Sink
from ..port import Port, PortDirection
from ...networking import send_http_data


import numpy as np



class DataLogger(Sink):
    def __init__(self):
        ports = [Port(PortDirection.INPUT, 4)]

        self.ip = None
        self.port = None

        super().__init__("logger", ports)

    def register_block(self, ip: str = "", port: int = 0):
        self.ip = ip
        self.port = port

        return super().register_block()


    def read(self) -> tuple[np.ndarray, np.ndarray]:
        SAMPLE_RATE = 5e12
        time_step = 1 / SAMPLE_RATE

        content_bytes = send_http_data(bytearray([0x01]), "api/datalogger", self.ip, self.port)
        content_samples = int(len(content_bytes) / 2)
        content_array = np.frombuffer(content_bytes, dtype=np.int16, count=content_samples)

        time_array = np.arange(0, content_samples * time_step, time_step)

        return content_array, time_array



    def __str__(self):
        output = ""
        output += f"[Data Logger]\n"

        for port in self.ports:
            output += f"\t\t{str(port)}\n"
    
        return output