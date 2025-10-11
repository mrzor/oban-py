from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._producer import Producer
    from ._query import Query


class Stager:
    def __init__(
        self,
        *,
        query: Query,
        producers: dict[str, Producer],
        stage_interval: float = 1.0,
        stage_limit: int = 20_000,
    ) -> None:
        self._query = query
        self._producers = producers
        self._stage_interval = stage_interval
        self._stage_limit = stage_limit

        self._loop_task = None

    async def start(self) -> None:
        self._loop_task = asyncio.create_task(self._loop(), name="oban-stager")

    async def stop(self) -> None:
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            try:
                await self._stage()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

            await asyncio.sleep(self._stage_interval)

    async def _stage(self) -> None:
        await self._query.stage_jobs(self._stage_limit)

        available = await self._query.check_available_queues()

        for queue in available:
            if queue in self._producers:
                await self._producers[queue].notify()
