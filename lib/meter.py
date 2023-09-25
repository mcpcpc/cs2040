#!/usr/bin/env python
# -*- coding: utf-8 -*-

import machine

from pimoroni import Analog
from pimoroni import AnalogMux
from plasma import WS2812
from servo import servo2040


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

    @classmethod
    def get_hue(self, index: int) -> float:
        """Computer and return LED meter hue value."""

        hue = (1.0 - index / (self.num_leds - 1)) * 0.333
        return float(hue)

    @classmethod
    def get_level(self, index: int) -> float:
        """Computer and return LED meter level value."""

        level = (index + 0.5) / self.num_leds
        return float(level)

    @classmethod
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