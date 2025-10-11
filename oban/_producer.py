from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ._backoff import jittery_clamped
from ._worker import resolve_worker
from .job import Job
from .types import Cancel, Snooze

if TYPE_CHECKING:
    from ._query import Query


class Producer:
    def __init__(
        self,
        *,
        query: Query,
        node: str,
        queue: str = "default",
        limit: int = 10,
        uuid: str,
    ) -> None:
        self._query = query
        self._node = node
        self._queue = queue
        self._limit = limit
        self._uuid = uuid

        self._jobs_available = asyncio.Event()
        self._loop_task = None
        self._running_jobs = set()

    async def start(self) -> None:
        self._loop_task = asyncio.create_task(
            self._loop(), name=f"oban-producer-{self._queue}"
        )

    async def stop(self) -> None:
        if self._loop_task:
            self._loop_task.cancel()

            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

        if self._running_jobs:
            await asyncio.gather(*self._running_jobs, return_exceptions=True)

    async def notify(self) -> None:
        self._jobs_available.set()

    async def _loop(self) -> None:
        while True:
            try:
                # TODO: Shorten this timeout based on configuration, the timeout changes whether we
                # cleanly break on a stop event
                await asyncio.wait_for(self._jobs_available.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            self._jobs_available.clear()

            try:
                demand = self._limit - len(self._running_jobs)

                if demand <= 0:
                    continue

                jobs = await self._fetch_jobs(demand)

                for job in jobs:
                    task = asyncio.create_task(self._execute(job))
                    task.add_done_callback(self._running_jobs.discard)

                    self._running_jobs.add(task)

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _fetch_jobs(self, demand: int):
        return await self._query.fetch_jobs(
            demand=demand,
            queue=self._queue,
            node=self._node,
            uuid=self._uuid,
        )

    async def _execute(self, job: Job) -> None:
        worker = resolve_worker(job.worker)()

        try:
            result = await asyncio.to_thread(worker.process, job)
        except Exception as error:
            result = error

        match result:
            case Exception() as error:
                backoff = self._backoff(worker, job)
                await self._query.error_job(job, error, backoff)
            case Snooze(seconds=seconds):
                await self._query.snooze_job(job, seconds)
            case Cancel(reason=reason):
                await self._query.cancel_job(job, reason)
            case _:
                await self._query.complete_job(job)

    def _backoff(self, worker: Any, job: Job) -> int:
        if hasattr(worker, "backoff"):
            return worker.backoff(job)
        else:
            return jittery_clamped(job.attempt, job.max_attempts)
