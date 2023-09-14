#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import machine
import uasyncio

from pimoroni import Analog
from pimoroni import AnalogMux
from plasma import WS2812
from servo import servo2040
from servo import ServoCluster


def get_hue(num_leds: int, i: int) -> float:
    """Get LED hue based on LED index."""

    hue = (1.0 - i / (num_leds - 1)) * 0.333
    return hue


def get_level(num_leds: int, i: int) -> float:
    """Get LED level based on LED index."""

    level = (i + 0.5) / num_leds
    return level


def create_servo_cluster() -> ServoCluster:
    """Create and return new ServoCluster object."""

    gc.collect()
    start = servo2040.SERVO_1
    end = servo2040.SERVO_1
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

    async def step(self, cluster) -> None:
        """Step servo motors to new position."""

        cluster.all_to_min()
        await uasyncio.sleep_ms(2000)
        cluster.all_to_max()
        await uasyncio.sleep_ms(2000)

    async def run(self) -> None:
        """Run servo motors in process loop."""

        cluster = create_servo_cluster()
        while True:
            await self.step(cluster)
            await uasyncio.sleep_ms(200)


class ServoCurrentMeter:
    """Servo current meter representation."""

    async def get_measurement(self, adc: Analog) -> float:
        """Get measurement from ADC object."""

        current = 0.0
        for i in range(5):
            current += adc.read_current()
            await uasyncio.sleep_ms(200)
        current_average = current / 5
        return current_average

    async def step(self) -> None:
        """Step through current measurement process."""

        

    async def run(self) -> None:
        """Run servo current meter in loop."""

        leds = create_leds()
        current_adc = create_current_adc()
        analog_mux = create_analog_mux()
        analog_mux.select(servo2040.CURRENT_SENSE_ADDR)


async def main():
    sweepers = ChimneySweepers()
    meter = ServoCurrentMeter()
    uasyncio.create_task(sweepers.run())
    #uasyncio.create_task(meter.run())
    while True:
        await uasyncio.sleep_ms(200)


if __name__ == "__main__":
    uasyncio.run(main())
