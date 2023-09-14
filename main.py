#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import uasyncio

from servo import servo2040
from servo import ServoCluster


class ChimneySweepers:
    """Chimney sweepers representation."""

    async def create(self) -> ServoCluster:
        """Create and return new ServoCluster object."""

        gc.collect()
        start = servo2040.SERVO_1
        end = servo2040.SERVO_1
        pins = list(range(start, end + 1))
        cluster = ServoCluster(0, 0, pins)
        return cluster

    async def step(self, cluster) -> None:
        """Step servo motors to new position."""

        cluster.all_to_min()
        await uasyncio.sleep_ms(2000)
        cluster.all_to_max()
        await uasyncio.sleep_ms(2000)

    async def run(self) -> None:
        """Run servo motors in process loop."""

        cluster = await self.create()
        while True:
            await self.step(cluster)
            await uasyncio.sleep_ms(200)


async def main():
    sweepers = ChimneySweepers()
    uasyncio.create_task(sweepers.run())
    while True:
        # read meter
        await uasyncio.sleep_ms(200)


if __name__ == "__main__":
    uasyncio.run(main())
