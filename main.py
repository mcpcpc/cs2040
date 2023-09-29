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
    end = servo2040.SERVO_2
    pins = list(range(start, end + 1))
    return ServoCluster(0, 0, pins)


def create_leds() -> WS2812:
    """Create and return WS2812 array."""
 
    leds = WS2812(
        num_leds=servo2040.NUM_LEDS,
        pio=1,
        sm=0,
        dat=servo2040.LED_DATA,
    )
    return leds


def create_current_adc() -> Analog:
    """Create and return current ADC."""

    current_adc = Analog(
        servo2040.SHARED_ADC,
        servo2040.CURRENT_GAIN,
        servo2040.SHUNT_RESISTOR,
        servo2040.CURRENT_OFFSET,
    )
    return current_adc


def create_analog_mux() -> AnalogMux:
    """Create and return analog multiplexer."""

    muxed_pin = machine.Pin(servo2040.SHARED_ADC)
    analog_mux = AnalogMux(
        servo2040.ADC_ADDR_0,
        servo2040.ADC_ADDR_1,
        servo2040.ADC_ADDR_2,
        muxed_pin=muxed_pin,
    )
    return analog_mux


class LoadCurrentMeter:
    """Servo current meter representation."""

    max_load = 3.0 # amperes
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
        """Computer and return LED meter hue value."""

        hue = (1.0 - index / (self.num_leds - 1)) * 0.333
        return float(hue)

    def get_level(self, index: int) -> float:
        """Computer and return LED meter level value."""

        level = (index + 0.5) / self.num_leds
        return float(level)

    def get_load(self, value: float) -> float:
        """Computer and return current load utilization."""

        load = value / self.max_load
        return float(load)

    def initialize(self) -> None:
        """Initialize current meter."""

        self.mux.select(servo2040.CURRENT_SENSE_ADDR)
        self.leds.start()

    def step(self) -> None:
        """Step through current measuremsent process."""

        current = self.adc.read_current()
        percent = self.get_load(current)
        for i in range(self.num_leds):
            hue = self.get_hue(i)
            level = self.get_level(i)
            if percent >= level:
                self.leds.set_hsv(
                    i,
                    hue,
                    1.0,
                    self.brightness_on,
                )
            else:
                self.leds.set_hsv(
                    i,
                    hue,
                    1.0,
                    self.brightness_off,
                ) 

    def run(self) -> None:
        """Run servo current meter in loop."""

        self.initialize()
        while True:
            self.step()


class TranslateBase:
    """Translation base representation."""

    start: float = -1.0
    end: float = 1.0
    duration_ms: int = 2000

    def __call__(self, time_ms: int) -> float:
        return self.ease(time_ms)

    def function(self, t: float) -> int:
        """User implemented translation function."""

        return NotImplementedError

    def ease(self, time_ms: int) -> float:
        """Ease postion from current time in milliseconds."""

        a = self.function(time_ms / self.duration_ms)
        return a * (self.end - self.start) + self.start


class Linear(TranslateBase):
    """Linear translation representation."""

    def function(self, t: float) -> float:
        return t


class ServoTickBase:

    start_ms: int = 0

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

    def tick(self, servo: int) -> bool:
        """Single tick in motion."""

        ellapsed_ms = time.ticks_ms() - self.start_ms
        if ellapsed_ms > self.translate.duration_ms:
            position = self.translate.end
            self.cluster.to_percent(
                servo,
                position,
                self.translate.start,
                self.translate.end,
            )
            return True
        position = self.translate.ease(ellapsed_ms)
        self.cluster.to_percent(
            servo,
            position,
            self.translate.start,
            self.translate.end,
        )
        if position == self.translate.end:
            return True
        return False



class ChimneySweepers(ServoTickBase):
    """Chimney sweepers representation."""

    sequence: list = [
        [-1.0, 1.0],
        [1.0, -1.0],
    ]

    def tick_all(self, seq: list, prev: list) -> list[bool]:
        """Tick all."""
        
        result = []
        servos = range(self.cluster.count())
        for servo, start, end in zip(servos, prev, seq):
            print(f"{servo} {start} {end}")
            self.translate.start = start
            self.translate.end = end
            result.append(self.tick(servo))
        return result

    def setup(self) -> None:
        """Servo setup."""

        count = self.cluster.count()
        for servo in range(count):
            self.cluster.to_min()
            #self.cluster.to_percent(servo, -1.0, -1.0, 1.0)
            time.sleep_ms(1000)

    def step(self) -> None:
        """Step servo position."""

        self.start_ms = time.ticks_ms()
        for s, seq in enumerate(self.sequence):
            prev = self.sequence[s - 1]
            status = [False] * self.cluster.count()
            self.initialize()
            while not all(status):
                status = self.tick_all(seq, prev)

    def run(self) -> None:
        """Run servo motors in process loop."""

        while True:
            self.step()
            time.sleep_ms(200)


def main():
    """Main method for task scheduling."""

    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    cluster = create_servo_cluster()
    translate = Linear()
    sweepers = ChimneySweepers(cluster, translate)
    meter = LoadCurrentMeter(leds, adc, mux)
    _thread.start_new_thread(meter.run, ())
    sweepers.setup()
    sweepers.run()


if __name__ == "__main__":
    main()
