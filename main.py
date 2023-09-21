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


def get_hue(num_leds: int, index: int) -> float:
    """Computer and return LED meter hue value."""

    hue = (1.0 - index / (num_leds - 1)) * 0.333
    return hue


def get_level(num_leds: int, index: int) -> float:
    """Computer and return LED meter level value."""

    level = (index + 0.5) / num_leds
    return level


def get_load(current: float, max_current: float) -> float:
    """Computer and return current load utilization."""

    load = current / max_current
    return load


def create_servo_cluster() -> ServoCluster:
    """Create and return new ServoCluster object."""

    gc.collect()
    start = servo2040.SERVO_1
    end = servo2040.SERVO_7
    pins = list(range(start, end + 1))
    cluster = ServoCluster(0, 0, pins)
    return cluster


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


class ChimneySweepers:
    """Chimney sweepers representation."""
    
    step_delay = 5000 # milliseconds

    def __init__(self, cluster: ServoCluster) -> None:
        self.cluster = cluster

    def step(self) -> None:
        """Step servo sequence."""

        count = self.cluster.count()
        for servo in range(count):
            if (servo % 2) == 0:
                self.cluster.to_percent(servo, -1.0)
            else:
                self.cluster.to_percent(servo, 1.0)
            time.sleep_ms(300)
        time.sleep_ms(self.step_delay)
        for servo in range(count):
            if (servo % 2) == 0:
                self.cluster.to_percent(servo, 1.0)
            else:
                self.cluster.to_percent(servo, -1.0)
            time.sleep_ms(300)
        time.sleep_ms(self.step_delay)

    def run(self) -> None:
        """Run servo motors in process loop."""

        while True:
            self.step()
            time.sleep_ms(200)


class LoadCurrentMeter:
    """Servo current meter representation."""

    max_load = 3.0 # amperes
    num_leds = servo2040.NUM_LEDS 
    brightness_on = 0.4
    brightness_off = 0.1

    def __init__(self, leds: WS2812, adc: Analog, mux: AnalogMux) -> None:
        self.leds = leds
        self.adc = adc
        self.mux = mux

    def initialize(self) -> None:
        """Initialize current meter."""

        self.mux.select(servo2040.CURRENT_SENSE_ADDR)
        self.leds.start()

    def step(self) -> None:
        """Step through current measuremsent process."""

        current = self.adc.read_current()
        percent = get_load(current, self.max_load)
        for i in range(self.num_leds):
            hue = get_hue(self.num_leds, i)
            level = get_level(self.num_leds, i)
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


def main():
    """Main method for task scheduling."""

    cluster = create_servo_cluster()
    sweepers = ChimneySweepers(cluster)
    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    meter = LoadCurrentMeter(leds, adc, mux)
    _thread.start_new_thread(meter.run, ())
    sweepers.run()


if __name__ == "__main__":
    main()
