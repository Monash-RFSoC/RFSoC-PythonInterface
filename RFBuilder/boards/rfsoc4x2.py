from .boards import Board
from ..control import ControlPin, PinDict

class RFSOC4x2(Board):
    def __init__(self):
        super().__init__()

    def get_dacs(self):
        return [{"name" : "dac_a", "id" : 1}, {"name" : "dac_b", "id" : 0}]

    def get_adcs(self):
        return [{"name" : "adc_b", "id" : 4}, {"name" : "adc_d", "id" : 1}]
    
    def get_ttl_pins(self):
        ttl_pins = PinDict({
            "io": PinDict({
                "key": [
                    ControlPin("KEY0", 0, ControlPin.INPUT),
                    ControlPin("KEY1", 1, ControlPin.INPUT),
                    ControlPin("KEY2", 2, ControlPin.INPUT),
                    ControlPin("KEY3", 3, ControlPin.INPUT),
                ],
                "syzygy": [
                    ControlPin("SYZYGY_IN0", 8, ControlPin.INPUT),
                    ControlPin("SYZYGY_IN1", 9, ControlPin.INPUT),
                    ControlPin("SYZYGY_IN2", 10, ControlPin.INPUT),
                    ControlPin("SYZYGY_IN3", 11, ControlPin.INPUT),
                    ControlPin("SYZYGY_OUT0", 14, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT1", 15, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT2", 16, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT3", 17, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT4", 18, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT5", 19, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT6", 20, ControlPin.OUTPUT),
                    ControlPin("SYZYGY_OUT7", 21, ControlPin.OUTPUT),
                ],
                "led": [
                    ControlPin("LED0", 0, ControlPin.OUTPUT),
                    ControlPin("LED1", 1, ControlPin.OUTPUT),
                    ControlPin("LED2", 2, ControlPin.OUTPUT),
                    ControlPin("LED3", 3, ControlPin.OUTPUT),
                ]
            }),
            "software": [
                ControlPin("SOFTWARE0", 4, ControlPin.INPUT, software_controlled=True),
                ControlPin("SOFTWARE1", 5, ControlPin.INPUT, software_controlled=True),
                ControlPin("SOFTWARE2", 6, ControlPin.INPUT, software_controlled=True),
                ControlPin("SOFTWARE3", 7, ControlPin.INPUT, software_controlled=True),
            ],
            "PULSE_BLASTER": [
                ControlPin("PB_FLAG0", 12, ControlPin.INPUT),
                ControlPin("PB_FLAG1", 13, ControlPin.INPUT),
                ControlPin("PB_FLAG2", 14, ControlPin.INPUT),
                ControlPin("PB_FLAG3", 15, ControlPin.INPUT),
                ControlPin("PB_FLAG4", 16, ControlPin.INPUT),
                ControlPin("PB_FLAG5", 17, ControlPin.INPUT),
                ControlPin("PB_FLAG6", 18, ControlPin.INPUT),
                ControlPin("PB_FLAG7", 19, ControlPin.INPUT),
                ControlPin("PB_FLAG8", 20, ControlPin.INPUT),
                ControlPin("PB_FLAG9", 21, ControlPin.INPUT),
                ControlPin("PB_FLAG10", 22, ControlPin.INPUT),
                ControlPin("PB_FLAG11", 23, ControlPin.INPUT),

                ControlPin("PB_RUN", 8, ControlPin.OUTPUT),
                ControlPin("PB_TRIG", 9, ControlPin.OUTPUT),
                ControlPin("PB_RSTN", 10, ControlPin.OUTPUT),
                ControlPin("PB_ISR", 1, ControlPin.OUTPUT),
            ],
            "logger": [
                ControlPin("DIGITIZER_TRIG0", 4, ControlPin.OUTPUT),
                ControlPin("DIGITIZER_TRIG1", 5, ControlPin.OUTPUT),
                ControlPin("DIGITIZER_TRIG2", 6, ControlPin.OUTPUT),
                ControlPin("DIGITIZER_TRIG3", 7, ControlPin.OUTPUT),
            ],
            "loopback": [
                ControlPin("LOOPBACK_IN0", 27, ControlPin.INPUT),
                ControlPin("LOOPBACK_IN1", 28, ControlPin.INPUT),
                ControlPin("LOOPBACK_IN2", 29, ControlPin.INPUT),
                ControlPin("LOOPBACK_IN3", 30, ControlPin.INPUT),

                ControlPin("LOOPBACK_OUT0", 27, ControlPin.OUTPUT),
                ControlPin("LOOPBACK_OUT1", 28, ControlPin.OUTPUT),
                ControlPin("LOOPBACK_OUT2", 29, ControlPin.OUTPUT),
                ControlPin("LOOPBACK_OUT3", 30, ControlPin.OUTPUT)
            ]

        })

        return ttl_pins

    
    def __str__(self) -> str:
        return "RFSoC4x2"
