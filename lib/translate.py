#!/usr/bin/env python
# -*- coding: utf-8 -*-


class TranslateBase:
    """Translation base representation."""

    def __init__(
        self,
        start: float = -1.0,
        end: float = 1.0,
        duration_ms: int = 1000,
     ) -> None:
        self.start = float(start)
        self.end = float(end)
        self.duration_ms = int(duration_ms)

    def __call__(self, time_ms: int) -> float:
        return self.ease(time_ms)

    def function(self, t: float) -> int:
        """User implemented translation function."""

        return NotImplementedError

    @classmethod
    def ease(self, time_ms: int) -> float:
        """Ease postion from current time in milliseconds."""

        a = self.function(time_ms / self.duration_ms)
        return a * (self.end - self.start) + self.start
