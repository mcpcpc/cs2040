#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


class TranslationBase:
    """Translation base representation."""

    def __init__(
        self,
        start: float,
        end: float,
        duration_ms: int
     ) -> None:
        self.start = start
        self.end = end
        self.duration_ms = duration_ms

    def __call__(self, time_ms: int) -> float:
        return self.ease(time_ms)

    def function(self, t: float) -> int:
        return NotImplementedError
 
    def ease(self, time_ms: int) -> float:
        a = self.function(time_ms / self.duration_ms)
        return (self.end * a) + self.start * (1 - a)


class Linear(TranslationBase):
    """Linear translation representation."""

    def function(self, t: float) -> int:
        return t

 
 class ServoClusterTranslate:
    """Servo translate representation."""

    start: float = -1.0
    end: float = 1.0
    duration: int = 1000
    transition: TransitionBase = Linear(
        start=self.start,
        end=self.end,
        duration=self.duration,
    )
    current_time: int = 0
    start_time: int = 0

    def __init__(self, servo) -> None:
        self.servo = servo

    def tick_start(self) -> None:
        """Servo tick start."""

        self.start_time = time.ticks_ms()
        self.transition.start = self.start
        self.transition.end = self.end
        self.transition.duration = self.duration

    def tick(self, servo) -> bool:
        """Servo tick."""

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