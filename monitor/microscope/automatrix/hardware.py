class AutomatrixHardware:
    TRIGGER = 25
    ACTIVE_HIGH = True
    SPI_CHANNEL = 0
    SPI_SPEED = 500000
    # LED re-numbering. Regular LED_idx is placed at the (regular) location
    # of led_map_forward[LED_idx] this is needed due to a hardware decision # of routing the LED to
    # the nearest output of the shift-register
    LED_MAP = {
        7: 4,
        6: 5,
        5: 6,
        4: 7,
        3: 3,
        2: 2,
        1: 1,
        0: 0,
    }
    # matrix dimension (square)
    MATRIX_DIM = 16
    # Parallel outputs for the number of shift registers
    PARALLEL_OUT = 8
    # number of shift registers
    SHIFTERS = MATRIX_DIM**2//PARALLEL_OUT
