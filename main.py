#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""main.py: CS-2040 Servo Controller Module"""

# MicroPython built-in libraries
from collections import deque
from gc import collect
from machine import Pin
from neopixel import NeoPixel
from time import sleep_ms
from time import ticks_diff
from time import ticks_ms
from _thread import start_new_thread
from _thread import allocate_lock
from _thread import LockType

# Pimoroni libraries
from pimoroni import Analog
from pimoroni import AnalogMux
from plasma import WS2812
from servo import servo2040
from servo import Servo

__version__ = "1.0.0"

RGBW_BLACK = const((0, 0, 0, 0))
RGBW_RED = const((255, 0, 0, 0))
RGBW_ORANGE = const((255, 40, 0, 0))
RGBW_YELLOW = const((255, 150, 0, 0))
RGBW_GREEN = const((0, 255, 0, 0))
RGBW_BLUE = const((0, 0, 255, 0))
RGBW_VIOLET = const((180, 0, 255, 0))


def create_leds() -> WS2812:
    """Create and return WS2812 array."""
 
    return WS2812(
        num_leds=servo2040.NUM_LEDS,
        pio=1,
        sm=0,
        dat=servo2040.LED_DATA,
    )


def create_current_adc() -> Analog:
    """Create and return current ADC."""

    return Analog(
        servo2040.SHARED_ADC,
        servo2040.CURRENT_GAIN,
        servo2040.SHUNT_RESISTOR,
        servo2040.CURRENT_OFFSET,
    )


def create_analog_mux() -> AnalogMux:
    """Create and return analog multiplexer."""

    muxed_pin = Pin(servo2040.SHARED_ADC)
    return AnalogMux(
        servo2040.ADC_ADDR_0,
        servo2040.ADC_ADDR_1,
        servo2040.ADC_ADDR_2,
        muxed_pin=muxed_pin,
    )


def create_rgbw_neopixels() -> NeoPixel:
    """Create and return neopixels."""

    din_pin = Pin(servo2040.SDA) 
    return NeoPixel(din_pin, 8, bpp=4)


class LoadCurrentMeter:
    """Servo current meter representation."""

    max_amperes = 3.0 # rated
    limit_amperes = 2.0 # safety factor
    num_leds = servo2040.NUM_LEDS 
    brightness_on = 0.4
    brightness_off = 0.1

    def __init__(
        self,
        leds: WS2812,
        adc: Analog,
        mux: AnalogMux,
    ) -> None:
        self.leds = leds
        self.adc = adc
        self.mux = mux

    def get_hue(self, index: int) -> float:
        """Compute and return LED HSV color hue."""

        hue = (1.0 - index / (self.num_leds - 1)) * 0.333
        return float(hue)

    def get_value(self, index: int, load: float) -> float:
        """Compute and return LED HSV color value."""

        level = (index + 0.5) / self.num_leds
        if load >= level:
            return self.brightness_on
        return self.brightness_off

    def step(self) -> bool:
        """Step through current measurement process."""

        current = self.adc.read_current()
        if current > self.limit_amperes:
            return False
        load = current / self.max_amperes
        for i in range(self.num_leds):
            h = self.get_hue(i)
            v = self.get_value(i, load)
            self.leds.set_hsv(i, h, 1.0, v)
        return True 

    def run(self, lock: LockType) -> None:
        """Run servo current meter in loop."""

        lock.acquire()
        self.mux.select(servo2040.CURRENT_SENSE_ADDR)
        self.leds.start()
        while self.step():
            continue
        lock.release() 


class SequenceBase:
    """Sequences representation."""

    def __init__(self, items: list) -> None:
        self.items = items
        maxlen = len(items)
        self.deque = deque((), maxlen)
        for item in items:
            self.deque.append(item)

    def __call__(self):
        """Rotate head to tail and return head."""

        head = self.deque.popleft()
        self.deque.append(head)
        return head


class ChimneySweepers:
    """Chimney sweepers representation."""
 
    start_ms: int = 0

    def __init__(
        self,
        neopixels: NeoPixel,
        sequences: SequenceBase,
        servo: Servo,
    ) -> None:
        self.neopixels = neopixels
        self.sequences = sequences
        self.servo = servo

    def step(self, sequences: list) -> None:
        """Servo step."""

        for servo, color in sequences:
            self.neopixels[servo] = color
        self.neopixels.write()

    def initialize(self, sequences: list) -> None:
        """Initialize servo position."""

        for servo, *_ in sequences:
            self.neopixels[servo] = RGBW_BLACK
        self.neopixels.write()
        self.servo.value(0.04)

    def run(self, lock: LockType) -> None:
        """Run servo motors in process loop."""

        head = self.sequences.items[0]
        self.initialize(head)
        while not lock.acquire(0):
            sequences = self.sequences()
            self.step(sequences)
            sleep_ms(5000)


def main():
    """Main method for task scheduling."""

    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    neopixels = create_rgbw_neopixels()
    servo = Servo(servo2040.SERVO_1, 2)
    sequences = SequenceBase(
        items=[
            [
                (0, RGBW_RED),
                (1, RGBW_BLACK),
                (2, RGBW_YELLOW),
                (3, RGBW_BLACK),
                (4, RGBW_BLUE),
                (5, RGBW_BLACK),
                (6, RGBW_VIOLET),
                (7, RGBW_BLACK),
            ],
            [
                (0, RGBW_BLACK),
                (1, RGBW_ORANGE),
                (2, RGBW_BLACK),
                (3, RGBW_GREEN),
                (4, RGBW_BLACK),
                (5, RGBW_VIOLET),
                (6, RGBW_BLACK),
                (7, RGBW_BLACK),
            ],
            [
                (0, RGBW_VIOLET),
                (1, RGBW_BLACK),
                (2, RGBW_ORANGE),
                (3, RGBW_BLACK),
                (4, RGBW_GREEN),
                (5, RGBW_BLACK),
                (6, RGBW_VIOLET),
                (7, RGBW_BLACK),
            ],
            [
                (0, RGBW_BLACK),
                (1, RGBW_RED),
                (2, RGBW_BLACK),
                (3, RGBW_YELLOW),
                (4, RGBW_BLACK),
                (5, RGBW_BLUE),
                (6, RGBW_BLACK),
                (7, RGBW_BLACK),
            ],
        ]
    )
    sweepers = ChimneySweepers(
        neopixels,
        sequences,
        servo,
    )
    meter = LoadCurrentMeter(leds, adc, mux)
    lock = allocate_lock()
    start_new_thread(meter.run, (lock,))
    sleep_ms(200)  # allow time for meter lock
    sweepers.run(lock)


if __name__ == "__main__":
    main()
