from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING
from uuid import uuid4

from ._executor import Executor
from .job import Job

if TYPE_CHECKING:
    from ._notifier import Notifier
    from ._query import Query


class Producer:
    def __init__(
        self,
        *,
        debounce_interval: float = 0.005,
        limit: int = 10,
        name: str,
        node: str,
        notifier: Notifier,
        query: Query,
        queue: str = "default",
    ) -> None:
        self._debounce_interval = debounce_interval
        self._limit = limit
        self._name = name
        self._node = node
        self._notifier = notifier
        self._query = query
        self._queue = queue

        self._executor = Executor(query, safe=True)
        self._last_fetch_time = 0.0
        self._listen_token = None
        self._loop_task = None
        self._notified = asyncio.Event()
        self._paused = False
        self._running_jobs = set()
        self._uuid = str(uuid4())

    async def start(self) -> None:
        await self._query.insert_producer(
            uuid=self._uuid,
            name=self._name,
            node=self._node,
            queue=self._queue,
            meta={"local_limit": self._limit},
        )

        self._listen_token = await self._notifier.listen(
            "signal", self._on_notification, wait=False
        )

        self._loop_task = asyncio.create_task(
            self._loop(), name=f"oban-producer-{self._queue}"
        )

    async def stop(self) -> None:
        if self._listen_token:
            await self._notifier.unlisten(self._listen_token)

        self._loop_task.cancel()

        await asyncio.gather(
            self._loop_task, *self._running_jobs, return_exceptions=True
        )

        await self._query.delete_producer(self._uuid)

    def notify(self) -> None:
        self._notified.set()

    async def pause(self) -> None:
        self._paused = True

        await self._query.update_producer(uuid=self._uuid, meta={"paused": True})

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.wait_for(self._notified.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            self._notified.clear()

            try:
                await self._debounce_fetch()

                if self._paused:
                    continue

                demand = self._limit - len(self._running_jobs)

                if demand <= 0:
                    continue

                jobs = await self._fetch_jobs(demand)

                self._last_fetch_time = asyncio.get_event_loop().time()

                for job in jobs:
                    task = asyncio.create_task(self._execute(job))
                    task.add_done_callback(self._on_job_complete)

                    self._running_jobs.add(task)

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _debounce_fetch(self) -> None:
        elapsed = asyncio.get_event_loop().time() - self._last_fetch_time

        if elapsed < self._debounce_interval:
            await asyncio.sleep(self._debounce_interval - elapsed)

    def _on_job_complete(self, task: asyncio.Task) -> None:
        self._running_jobs.discard(task)

        self.notify()

    async def _fetch_jobs(self, demand: int):
        return await self._query.fetch_jobs(
            demand=demand,
            queue=self._queue,
            node=self._node,
            uuid=self._uuid,
        )

    async def _execute(self, job: Job) -> None:
        await self._executor.execute(job)

    async def _on_notification(self, _channel: str, payload: dict) -> None:
        ident = payload.get("ident")

        if payload.get("queue") != self._queue:
            return

        # TODO: Encode the `ident` format somewhere else
        if ident != "any" and ident != f"{self._name}.{self._node}":
            return

        # TODO: Switch to match when there are other actions
        if payload.get("action") == "pause":
            await self.pause()
