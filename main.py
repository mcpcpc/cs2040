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
from servo import ServoCluster

__version__ = "1.0.0"

RGBW_BLACK = const((0, 0, 0, 0))
RGBW_RED = const((255, 0, 0, 0))
RGBW_ORANGE = const((255, 40, 0, 0))
RGBW_YELLOW = const((255, 150, 0, 0))
RGBW_GREEN = const((0, 255, 0, 0))
RGBW_BLUE = const((0, 0, 255, 0))
RGBW_VIOLET = const((180, 0, 255, 0))


def create_servo_cluster() -> ServoCluster:
    """Create and return new ServoCluster object."""

    collect()
    start = servo2040.SERVO_1
    end = servo2040.SERVO_8
    pins = list(range(start, end + 1))
    return ServoCluster(0, 0, pins)


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


class TranslateBase:
    """Translation base representation."""

    start: float = -1.0
    end: float = 1.0
    duration_ms: int = 5000

    def __call__(self, time_ms: int) -> float:
        return self.ease(time_ms)

    def function(self, t: float) -> int:
        """User implemented translation function."""

        return NotImplementedError

    def ease(self, time_ms: int) -> float:
        """Ease postion from current time in milliseconds."""

        a = self.function(time_ms / self.duration_ms)
        return a * (self.end - self.start) + self.start


class Ease_in_quad(TranslateBase):
    """Quadratic ease-in function."""

    def function(self, t: float) -> float:
        return t * t


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
        cluster: ServoCluster,
        neopixels: NeoPixel,
        sequences: SequenceBase,
        translate: TranslateBase,
    ) -> None:
        self.cluster = cluster
        self.neopixels = neopixels
        self.sequences = sequences
        self.translate = translate

    def to_position(self, servo: int, position: float) -> None:
        """Trigger servo to position."""

        self.cluster.to_percent(servo, position, -1.0, 1.0)

    def tick(self, servo: int) -> bool:
        """Single tick in motion."""

        now_ms = ticks_ms()
        ellapsed_ms = ticks_diff(now_ms, self.start_ms)
        if ellapsed_ms > self.translate.duration_ms:
            position = self.translate.end
            self.to_position(servo, position)
            return True  # exceeded ellapsed_time
        position = self.translate.ease(ellapsed_ms)
        self.to_position(servo, position)
        if position == self.translate.end:
            return True  # reached end position
        return False  # next tick

    def step(self, sequences: list) -> None:
        """Servo step."""

        status = [False]
        self.start_ms = ticks_ms()
        while not all(status):
            status = []
            for servo, start, end, duration, color in sequences:
                self.translate.start = start
                self.translate.end = end
                self.translate.duration_ms = duration
                status.append(self.tick(servo))
                self.neopixels[servo] = color
        self.neopixels.write()

    def initialize(self, sequences: list) -> None:
        """Initialize servo position."""

        for servo, start, *_ in sequences:
            sleep_ms(500)
            self.to_position(servo, start)
            self.neopixels[servo] = RGBW_BLACK
        self.neopixels.write()

    def run(self, lock: LockType) -> None:
        """Run servo motors in process loop."""

        head = self.sequences.items[0]
        self.initialize(head)
        sleep_ms(3000)
        while not lock.acquire(0):
            sequences = self.sequences()
            self.step(sequences)


def main():
    """Main method for task scheduling."""

    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    neopixels = create_rgbw_neopixels()
    cluster = create_servo_cluster()
    sequences = SequenceBase(
        items=[
            [
                (0, -1.0, 1.0, 5000, RGBW_RED),
                (1, 1.0, -1.0, 5000, RGBW_BLACK),
                (2, -1.0, 1.0, 5000, RGBW_YELLOW),
                (3, 1.0, -1.0, 5000, RGBW_BLACK),
                (4, -1.0, 1.0, 5000, RGBW_BLUE),
                (5, 1.0, -1.0, 5000, RGBW_BLACK),
                (6, -1.0, 1.0, 5000, RGBW_VIOLET),
                (7, -1.0, 0.5, 5000, RGBW_BLACK),
            ],
            [
                (0, 1.0, -1.0, 5000, RGBW_BLACK),
                (1, -1.0, 1.0, 5000, RGBW_ORANGE),
                (2, 1.0, -1.0, 5000, RGBW_BLACK),
                (3, -1.0, 1.0, 5000, RGBW_GREEN),
                (4, 1.0, -1.0, 5000, RGBW_BLACK),
                (5, -1.0, 1.0, 5000, RGBW_VIOLET),
                (6, 1.0, -1.0, 5000, RGBW_BLACK),
                (7, 0.5, -0.5, 5000, RGBW_BLACK),
            ],
            [
                (0, -1.0, 1.0, 5000, RGBW_VIOLET),
                (1, 1.0, -1.0, 5000, RGBW_BLACK),
                (2, -1.0, 1.0, 5000, RGBW_ORANGE),
                (3, 1.0, -1.0, 5000, RGBW_BLACK),
                (4, -1.0, 1.0, 5000, RGBW_GREEN),
                (5, 1.0, -1.0, 5000, RGBW_BLACK),
                (6, -1.0, 1.0, 5000, RGBW_VIOLET),
                (7, -0.5, 0.0, 5000, RGBW_BLACK),
            ],
            [
                (0, 1.0, -1.0, 5000, RGBW_BLACK),
                (1, -1.0, 1.0, 5000, RGBW_RED),
                (2, 1.0, -1.0, 5000, RGBW_BLACK),
                (3, -1.0, 1.0, 5000, RGBW_YELLOW),
                (4, 1.0, -1.0, 5000, RGBW_BLACK),
                (5, -1.0, 1.0, 5000, RGBW_BLUE),
                (6, 1.0, -1.0, 5000, RGBW_BLACK),
                (7, 0.0, -1.0, 5000, RGBW_BLACK),
            ],
        ]
    )
    translate = Ease_in_quad()
    sweepers = ChimneySweepers(
        cluster,
        neopixels,
        sequences,
        translate, 
    )
    meter = LoadCurrentMeter(leds, adc, mux)
    lock = allocate_lock()
    start_new_thread(meter.run, (lock,))
    sleep_ms(200)  # allow time for meter lock
    sweepers.run(lock)


if __name__ == "__main__":
    main()
