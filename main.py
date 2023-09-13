#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import uasyncio

from servo import servo2040
from servo import ServoCluster

SERVO_PIN_START = servo2040.SERVO_1
SERVO_PIN_END = servo2040.SERVO_1

gc.collect()


class ChimneySweepers:
    """Chimney sweepers representation."""

    def __init__(
        self,
        start: int = SERVO_PIN_START,
        stop: int = SERVO_PIN_END,
    ) -> None:
        self.start = start
        self.end = stop
        pins = list(range(self.start, self.end + 1))
        self.cluster = ServoCluster(0, 0, pins)

    async def step(self) -> None:
        await self.cluster.enable_all()
        await uasyncio.sleep_ms(200)
        await self.cluster.all_to_min()
        await uasyncio.sleep_ms(2000)
        await self.cluster.all_to_max()
        await uasyncio.sleep_ms(2000)
        await self.cluster.disable_all()

    async def run(self) -> None:
        while True:
            await self.step()
            await uasyncio.sleep_ms(200)


async def main() -> None:
    sweepers = ChimneySweepers()
    uasyncio.create_task(sweepers.run())


if __name__ == "__main__":
    uasyncio.run(main())