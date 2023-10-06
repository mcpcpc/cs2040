#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""main.py: CS-2040 Servo Controller Module"""

__author__ = "Michael Czigler"
__copyright__ = "Copyright 2023, Michael Czigler"
__version__ = "1.0.0"
__license__ = "BSD-3-Clause"
__status__ = "Production"

import gc
import machine
import time
import _thread

from pimoroni import Analog
from pimoroni import AnalogMux
from plasma import WS2812
from servo import servo2040
from servo import ServoCluster


def create_servo_cluster() -> ServoCluster:
    """Create and return new ServoCluster object."""

    gc.collect()
    start = servo2040.SERVO_1
    end = servo2040.SERVO_7
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

    muxed_pin = machine.Pin(servo2040.SHARED_ADC)
    return AnalogMux(
        servo2040.ADC_ADDR_0,
        servo2040.ADC_ADDR_1,
        servo2040.ADC_ADDR_2,
        muxed_pin=muxed_pin,
    )


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

    def get_value(self, index: int, load: float) -> None:
        """Compute and return LED HSV color value."""

        level = (index + 0.5) / self.num_leds
        if load >= level:
            return self.brightness_on
        return self.brightness_off

    def initialize(self) -> None:
        """Initialize current meter."""

        self.mux.select(servo2040.CURRENT_SENSE_ADDR)
        self.leds.start()

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

    def run(self, lock: _thread.Lock = None) -> None:
        """Run servo current meter in loop."""

        lock.acquire()
        self.initialize()
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


class ServoTickBase:
    """Servo tick base representation."""

    start_ms: int = 0
    min_position: float = -1.0
    max_position: float = 1.0

    def __init__(
        self,
        cluster: ServoCluster,
        translate: TranslateBase
    ) -> None:
        self.cluster = cluster
        self.translate = translate

    def initialize(self) -> None:
        """Initialization."""

        self.start_ms = time.ticks_ms()

    def to_position(self, servo: int, position: float) -> None:
        """Trigger servo to position."""

        self.cluster.to_percent(
            servo,
            position,
            self.min_position,
            self.max_position,
        )

    def tick(self, servo: int) -> bool:
        """Single tick in motion."""

        ellapsed_ms = time.ticks_ms() - self.start_ms
        if ellapsed_ms > self.translate.duration_ms:
            position = self.translate.end
            self.to_position(servo, position)
            return True  # exceeded ellapsed_time
        position = self.translate.ease(ellapsed_ms)
        self.to_position(servo, position)
        if position == self.translate.end:
            return True  # reached end position
        return False  # next tick



class ChimneySweepers(ServoTickBase):
    """Chimney sweepers representation."""

    sequence: list = [
        [-1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0],
        [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0],
    ]

    def setup(self) -> None:
        """Servo setup."""

        count = self.cluster.count()
        for servo in range(count):
            self.cluster.to_min(servo)
            time.sleep_ms(500)

    def tick_all(self, seq: list, prev: list) -> list[bool]:
        """Tick all."""
        
        result = []
        servos = range(self.cluster.count())
        for servo, start, end in zip(servos, prev, seq):
            self.translate.start = start
            self.translate.end = end
            result.append(self.tick(servo))
        return result

    def step(self) -> None:
        """Step servo position."""

        for s, seq in enumerate(self.sequence):
            prev = self.sequence[s - 1]
            status = [False] * self.cluster.count()
            self.initialize()
            while not all(status):
                status = self.tick_all(seq, prev)

    def run(self, lock: _thread.LockType) -> None:
        """Run servo motors in process loop."""

        if isinstance(lock, _thread.LockType):
            while not lock.acquire(0):
                self.step()


def main():
    """Main method for task scheduling."""

    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    cluster = create_servo_cluster()
    translate = Ease_in_quad()
    sweepers = ChimneySweepers(cluster, translate)
    meter = LoadCurrentMeter(leds, adc, mux)
    lock = _thread.allocate_lock()
    _thread.start_new_thread(meter.run, (lock,))
    time.sleep_ms(200) # allow time for meter lock
    sweepers.setup()
    sweepers.run(lock)


if __name__ == "__main__":
    main()
