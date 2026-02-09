from RFBuilder2 import RFBuilder, RFSOC4x2, ArbitraryWaveformGenerator, WaveType

def main():
    board = RFSOC4x2()

    rf_builder = RFBuilder(board, "192.168.2.69", 8080)
    
    dacs = rf_builder.get_dacs()
    
    adcs = rf_builder.get_adcs()
    
    
    rf_builder.register_connection(adcs[0], dacs[0])
 
    awg = ArbitraryWaveformGenerator(WaveType.SINE, 3999e6)
    
    rf_builder.register_block(awg)
    
    rf_builder.register_connection(awg, dacs[1])

    print(rf_builder)

    print(str(rf_builder.update()))





if __name__ == "__main__":
    main()
    
