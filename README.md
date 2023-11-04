# CS-2040

CS-2040 is an RP2040-based servo controller project for christmas tree display
automation. The CS- prefix stands for "Chimney Sweep" as this project was
primarily designed to articulate 3D figurines for a Mary Poppins themed ornament
using low cost micro servos. 

In addition to articulating the figures, servo current load monitoring was also
considered an important aspect of this project. Luckily, the board selected for
this project includes built-in current-sense functionality and six addressable
RGB LEDs, which allow active visualization of the connected load.

Lastly, in order to add dramatic affect, RGB lighting was added using the built-in
NeoPixel library. Individual LEDs can be programmed per sequenced motor and
coded to reflect a desired color at a specified sequence step.

## Assembly

### Tools

- USB-C to USB-C or appropriate USB-C adapter cable for programming and power

### Bill of Material

The following materials are required to assemble and program the CS2040
controller. Note that the quantity of servos is not specified as this should be
based on the project requirements.

- **Pimoroni Servo 2040** or similar RP2040-based servo controller
- **Tower Pro SG92R** digital (micro) servo, 5.0 volt operation, 180-degree
- **Adafruit 4776** NeoPixel PCB, RGBW

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
4. Download the CS-2040 source tarball from GitHub and extract the source files.
   Alternatively, use the `git clone https://github.com/mcpcpc/cs2040` command
   to clone the source repository.
5. Using a MicroPython compatible IDE, copy the `main.py` file to to the servo
   controller.

### Wiring

1. Connect the servo motor cables and to the corresponding servo motors.
   ![Servo Connection Schema](/docs/motor.svg)
2. Connect the LED cables per the connection schema below.
   ![LED Connection Schema](/docs/led.svg)
3. Install the motors and LEDs to the final location. Ensure that the
   orientation of the servo is alternating every even and odd motor position.
   For example, the servo motor at position #1 should be in the lowest
   position, #2 at the highest position, #3 at the lowest position, etc. **Do
   not plug in the servo controller power until the position of each motor
   has been verified**.

### Powering Up
 
Connect power to the servo controller. The servo motors may immediately begin
to move in order to establish a known starting position. After the initial
position of each motor is set, there is a 3 second delay before the
actual sequencing of the servos begins.

### Powering Down

Waiting until all motors have returned to their initial sequence position (i.e.
as described in the [wiring](#Wiring) section above and **then** unplug power
to the servo motor controller.

For transportation purposes, disconnect the motors in the reverse order of the
[wiring](#Wiring) section above.

## References

* https://github.com/mcpcpc/cs2040/releases/latest
* https://github.com/pimoroni/pimoroni-pico/releases/latest
* https://github.com/pimoroni/pimoroni-pico/blob/main/setting-up-micropython.md
