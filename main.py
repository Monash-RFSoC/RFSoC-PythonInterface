from RFBuilder2 import RFBuilder, RFSOC4x2

def main():
    board = RFSOC4x2()

    rf_builder = RFBuilder(board)

    print(rf_builder)

    print(str(rf_builder.export()))


if __name__ == "__main__":
    main()
    
