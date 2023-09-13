#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import uasyncio

from servo import servo2040
from servo import ServoCluster

DEFAULT_SERVO_PIN_START = servo2040.SERVO_1
DEFAULT_SERVO_PIN_END = servo2040.SERVO_1


class ChimneySweepers:
    def __init__(
            self,
            start: int = DEFAULT_SERVO_PIN_START,
            end: int = DEFAULT_SERVO_PIN_END,
        ) -> None:
        self.start = start
        self.end = end

    def create(self) -> ServoCluster:
        gc.collect()
        pins = list(range(self.start, self.end + 1))
        cluster = ServoCluster(0, 0, pins)
        return cluster

    async def run(self) -> None:
        cluster = self.create()
        while True:
            cluster.enable_all()
            await uasyncio.sleep_ms(2000)
            cluster.all_to_min()
            await uasyncio.sleep(2)
            cluster.all_to_max()
            await uasyncio.sleep(2)
            cluster.disable_all()
            await uasyncio.sleep_ms(2000)


async def main():
    sweepers = ChimneySweepers()
    uasyncio.create_task(sweepers.run())
    while True:
        # read meter
        await uasyncio.sleep_ms(200)


if __name__ == "__main__":
    uasyncio.run(main())
