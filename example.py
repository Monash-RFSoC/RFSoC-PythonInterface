import time

from RFBuilder import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType, MicroBlaster, Mixer

board = RFSOC4x2()

rfb = RFBuilder(board, "169.254.127.84", 8080)

dacs = rfb.get_dacs()
adcs = rfb.get_adcs()

rfb.ttl.reset()

rfb.ttl.connect("SOFTWARE0", ["SYZYGY_OUT7", "SYZYGY_OUT4"])
rfb.ttl.connect(["SYZYGY_IN0", "SYZYGY_IN1"], ["SYZYGY_OUT5", "SYZYGY_OUT6"])
# rfb.ttl.connect("SOFTWARE2", ["SYZYGY_OUT5"])
# rfb.ttl.connect("SOFTWARE3", ["SYZYGY_OUT4"])


rfb.update()



while True:
    rfb.ttl.update_state("SOFTWARE0", 2)
    # time.sleep(0.01)
    # rfb.ttl.update_state("SOFTWARE1", 2)
    # # time.sleep(0.01)
    # rfb.ttl.update_state("SOFTWARE2", 2)
    # # time.sleep(0.01)
    # rfb.ttl.update_state("SOFTWARE3", 2)
    # # time.sleep(0.01)
    
