#!/usr/bin/env python
# -*- coding: utf-8 -*-


class SequenceBase:
    """Sequence base representation."""

    take: int = 8  # sequence length per iteration
    minimum: float = -1.0  # mininum position value
    maximum: float = 1.0  # maximum position value

    def __call__(self):
        result = self.generator(self.sequence())
        return result

    def sequence(self) -> bytearray:
        """User implemented sequence."""

        return NotImplementedError

    @classmethod
    def normalize(self, value: int) -> float:
        """Normalize sequence value."""

        normal_value = value / 0xFF
        return normal_value

    @classmethod
    def position(self, value: float) -> float:
        """Compute position from normalized value."""

        delta = self.maximum - self.minimum
        position = value * delta + self.minimum
        return float(position)

    @classmethod
    def generator(self, value: bytearray):
        """Positional array generator."""
        length = len(value)
        for i in range(0, length, self.take):
            seq = value[i:i + self.take]
            norm = list(map(self.normalize, seq))
            yield list(map(self.position, norm))


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
