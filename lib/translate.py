#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from servo import ServoCluster


class TranslationBase:
    """Translation base representation."""

    def __init__(
        self,
        start: float,
        end: float,
        duration_ms: int
     ) -> None:
        self.start = float(start)
        self.end = float(end)
        self.duration_ms = int(duration_ms)

    def __call__(self, time_ms: int) -> float:
        return self.ease(time_ms)

    def function(self, t: float) -> int:
        return NotImplementedError
 
    def ease(self, time_ms: int) -> float:
        a = self.function(int(time_ms) / self.duration_ms)
        return (self.end * a) + self.start * (1 - a)


class Linear(TranslationBase):
    """Linear translation representation."""

    def function(self, t: float) -> int:
        return t

 
 class ServoClusterTranslate:
    """Servo translate representation."""

    start_time: int = 0

    def __init__(
        self,
        servo: ServoCluster,
        translation: TransitionBase,
    ) -> None:
        self.servo = servo
        self.translate = translation

    def initialize(self) -> None:
        """Servo tick start."""

        self.start_time = time.ticks_ms()

    def tick(self, servo: int) -> bool:
        """Translation tick."""

        current_time = time.ticks_ms()
        ellapsed = time.ticks_diff(
            current_time,
            self.start_time,
        )
        if ellapsed > self.duration:
            current_position = self.end
            self.servo.to_position(
                servo,
                current_position,
            )
            return True
        current_position = self.transition.ease(ellapsed)
        self.servo.to_position(
            servo,
            current_position,
        )
        if current_position == self.end:
            return True
        else:
            return False

    def translate(self, servo: int) -> None:
        """Translate select servo in cluster."""

        self.initialize()
        while True:
            state = self.tick(servo)
            if status == True:
                break
