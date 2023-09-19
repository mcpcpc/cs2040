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
import uasyncio

from pimoroni import Analog
from pimoroni import AnalogMux
from plasma import WS2812
from servo import servo2040
from servo import ServoCluster

# servo parameters
SERVO_CLUSTER_PIN_START = servo2040.SERVO_1
SERVO_CLUSTER_PIN_END = servo2040.SERVO_7
SERVO_CLUSTER_DELAY = 5000 # in milliseconds

# meter parameters
METER_LOAD_MAX_AMPERES = 3.0
METER_LED_BRIGHTNESS_OFF = 0.1
METER_LED_BRIGHTNESS_ON = 0.5
METER_LED_NUMBER = servo2040.NUM_LEDS


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
    start = SERVO_CLUSTER_PIN_START
    end = SERVO_CLUSTER_PIN_END
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

    def __init__(self, cluster: ServoCluster) -> None:
        self.cluster = cluster

    async def step(self) -> None:
        """Step servo sequence."""

        count = self.cluster.count()
        for servo in range(count):
            if (servo % 2) == 0:
                self.cluster.to_min(servo)
            else:
                self.cluster.to_max(servo)
            await uasyncio.sleep_ms(500)
        await uasyncio.sleep_ms(SERVO_CLUSTER_DELAY)
        for servo in range(count):
            if (servo % 2) == 0:
                self.cluster.to_max(servo)
            else:
                self.cluster.to_min(servo)
            await uasyncio.sleep_ms(500)
        await uasyncio.sleep_ms(SERVO_CLUSTER_DELAY)

    async def run(self) -> None:
        """Run servo motors in process loop."""

        while True:
            await self.step()
            await uasyncio.sleep_ms(200)


class ServoCurrentMeter:
    """Servo current meter representation."""

    def __init__(self, leds: WS2812, adc: Analog, mux: AnalogMux) -> None:
        self.leds = leds
        self.adc = adc
        self.mux = mux

    async def step(self) -> None:
        """Step through current measuremsent process."""

        current = self.adc.read_current()
        percent = get_load(current, METER_LOAD_MAX_AMPERES)
        for i in range(METER_LED_NUMBER):
            hue = get_hue(METER_LED_NUMBER, i)
            level = get_level(METER_LED_NUMBER, i)
            if percent >= level:
                self.leds.set_hsv(i, hue, 1.0, METER_LED_BRIGHTNESS_ON)
            else:
                self.leds.set_hsv(i, hue, 1.0, METER_LED_BRIGHTNESS_OFF) 

    async def run(self) -> None:
        """Run servo current meter in loop."""

        self.mux.select(servo2040.CURRENT_SENSE_ADDR)
        self.leds.start()
        while True:
            await self.step()
            await uasyncio.sleep_ms(100)


async def main():
    """Main asynchronous method for task scheduling."""

    # Declare pin assignments and I/O objects
    cluster = create_servo_cluster()
    sweepers = ChimneySweepers(cluster)
    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    meter = ServoCurrentMeter(leds, adc, mux)
    # Initialize asynchronous tasks
    uasyncio.create_task(meter.run())
    await sweepers.run()


if __name__ == "__main__":
    uasyncio.run(main())
