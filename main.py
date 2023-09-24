#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""main.py: CS-2040 Servo Controller Module"""

__author__ = "Michael Czigler"
__copyright__ = "Copyright 2023, Michael Czigler"
__version__ = "1.0.0"
__license__ = "BSD-3-Clause"
__status__ = "Production"

import gc
import time
import _thread

from servo import servo2040
from servo import ServoCluster

from lib.meter import create_analog_mux
from lib.meter import create_current_adc
from lib.meter import create_leds
from lib.meter import LoadCurrentMeter
from lib.sequence import SequenceBase
from lib.translate import TranslateBase


def create_servo_cluster() -> ServoCluster:
    """Create and return new ServoCluster object."""

    gc.collect()
    start = servo2040.SERVO_1
    end = servo2040.SERVO_7
    pins = list(range(start, end + 1))
    return ServoCluster(0, 0, pins)


class Linear(TranslateBase):
    """Linear translation representation."""

    def function(self, t: float) -> int:
        return t


class AlternatingOctet(SequenceBase):
    """Alternating Octet
    
    Moves eight servos in alternating full-min nd full-max
    positions.

    """

    def sequence(self) -> bytearray:
        seq = [
            0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
            0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00
        ]
        return bytearray(seq)


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
