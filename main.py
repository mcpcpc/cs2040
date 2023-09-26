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
    """Alternating octet."""

    def sequence(self) -> bytearray:
        seq = [
            0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
            0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00
        ]
        return bytearray(seq)


class ChimneySweepers:
    """Chimney sweepers representation."""

    start_ms: int = 0

    def __init__(
        self,
        cluster: ServoCluster,
        sequence: SequenceBase,
        translate: TranslateBase
    ) -> None:
        self.cluster = cluster
        self.sequence = sequence
        self.translate = translate

    def tick(self, servo: int) -> bool:
        """Single tick in motion."""

        ellapsed_ms = time.ticks_diff(
            time.ticks_ms(),
            self.start_time,
        )
        if ellapsed_ms > self.translate.duration_ms:
            pos = self.translate.end
            self.cluster.to_position(servo, pos)
            return True
        pos = self.translate.ease(ellapsed_ms)
        self.cluster.to_position(servo, pos)
        if pos == self.end:
            return True
        return False

    def step(self) -> None:
        """Step servo position."""

        self.start_ms = time.ticks_ms()
        sequences = list(self.sequence())
        for s, seq in enumerate(sequences):
            status = [False] * len(seq)
            prev = sequences[s - 1]
            while not all(status):
                for i, pos in enumerate(seq):
                    self.translate.start = prev[i]
                    self.translate.end = pos
                    status[i] = self.tick(i)

    def run(self) -> None:
        """Run servo motors in process loop."""

        while True:
            self.step()
            time.sleep_ms(200)


def main():
    """Main method for task scheduling."""

    cluster = create_servo_cluster()
    sequence = AlternatingOctet()
    translate = Linear()
    sweepers = ChimneySweepers(
        cluster=cluster,
        sequence=sequence,
        translate=translate,
    )
    adc = create_current_adc()
    leds = create_leds()
    mux = create_analog_mux()
    meter = LoadCurrentMeter(leds, adc, mux)
    _thread.start_new_thread(meter.run, ())
    sweepers.run()


if __name__ == "__main__":
    main()
