from RFBuilder import RFBuilder, MemSource, LowPassFilter, WaveType, WaveGenerator
from RFBuilder.Boards import RFSoC4x2

import numpy as np


def main():
    rf_builder = RFBuilder()

    _temp1 = rf_builder.add_block(MemSource(base_address=0x00000000, stream_length=1024))
    _temp2 = rf_builder.add_block(LowPassFilter(fc=100e6))

    rf_builder.add_connection(source= _temp1, sink= _temp2)

    packet = rf_builder.construct_packet()
    
    RFSoC4x2.transmit(packet, "192.168.2.69", 8080)

    print(rf_builder)

    # sleep for 2 seconds
    import time
    time.sleep(3)

    data = {
        "request-type": "memory-stream",
        "data": np.random.randint(0, 256, size=1024).tolist()
    }

    RFSoC4x2.transmit(data, "192.168.2.69", 8080)

if __name__ == "__main__":
    main()