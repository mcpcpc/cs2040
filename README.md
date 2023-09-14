# CS-2040

CS-2040 is an RP2040-based servo controller project for christmas tree display
automation. The CS- prefix stands for "Chimney Sweep" as this project was
primarily designed to articulate 3D figurines for a Mary Poppins themed ornament
using low cost micro servos. The CS-2040 can support up to 18 consecutive 

In addition to articulating the figures, servo current load monitoring was also
considered an important aspect of this project. Luckily, the board selected for
this project includes built-in current-sense functionality and six addressable
RGB LEDs, which allow active visualization of the connected load.

## Assembly

### Bill of Material

The following materials are required to assemble and program the CS2040
controller. Note that the quantity of servos is not specified as this should be
based on the project requirements. Additionally, a USB-C adapter cable and PC
are required for initial programming and power.

- **Pimoroni Servo 2040** or similar RP2040-based servo controller
- **Tower Pro SG92R** digital (micro) servo, 5.0 volt operation, 180-deg
- **Bud Industries CU-18430-B** plastic enclosure, ABS, flanged

### Installation

1. Download the latest compiled MicroPython release from the pimoroni-pico
   repository. The selected `*.uf2` file should be chosen based on the target
   RP2040-based servo controller hardware. For example, for the Servo 2040
   board, the `pimoroni-pico-v1.XX.X-micropython.uf2` file would be appropriate.
2. While pressing and holding the *BOOT/USER* button, connect the RP2040 board
   to the computer usiing the USB-C adapter cable. This should automatically
   mount a new drive to your computer.
3. Replace any existing `*.uf2` file in the root directory of the mounted drive
   with the appropriate one downloaded in the first step. After the file is
   copied over, un-mount the drive, disconnect and reconnect the servo
   controller.

## References

* https://github.com/pimoroni/pimoroni-pico/releases/latest
