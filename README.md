# CS-2040

CS-2040 is an RP2040-based servo controller project for christmas tree display automation. The CS- prefix stands for "Chimney Sweep" as this project was initial designed to articulate 3D figurines for a Christmas tree display. 

## Assembly

### Bill of Material

The following materials are required to assemble and program the CS2040 controller. Note that the quantity of servos is not specified as this should be based on the project requirements. Additionally, a USB-C to USB-C cable is required for initial programming and power.

- Pimoroni Servo 2040 or similar RP2040-based servo controller
- Tower Pro SG92R digital (micro) servo, 5.0 volt operation
- Bud Industries CU-18430-B plastic enclosure, ABS, flanged

### Installation

1. Download the latest compiled micropython release from the pimoroni-pico repository. The selected `*.uf2` file should be chosen based on the target RP2040 servo controller hardware. For example, for the Servo 2040 board, the `pimoroni-pico-v1.XX.X-micropython.uf2` file would be appropriate.
2. Connect the RP2040 servo controller to 


## References

* https://github.com/pimoroni/pimoroni-pico/releases/latest
