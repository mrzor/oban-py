from typing import Any

from .job import Job
from .types import Result


def worker(*, oban=None, **overrides):
    """
    Decorate a class to make it a viable worker.
    """

    def decorate(cls: type) -> type:
        if not hasattr(cls, "perform"):

            def perform(self, job: Job) -> Result[Any]:
                raise NotImplementedError("Worker must implement perform method")

            setattr(cls, "perform", perform)

        @classmethod
        def new(cls, args: dict[str, Any], /, **overrides) -> Job:
            cfg = {**cls._opts, **overrides}
            return Job(worker=cls.__name__, args=args, **cfg)

        @classmethod
        def enqueue(cls, args: dict[str, Any], /, **overrides) -> Job:
            cfg = {**cls._opts, **overrides}
            job = Job(worker=cls.__name__, args=args, **cfg)

            return oban.enqueue(job)

        setattr(cls, "_opts", overrides)
        setattr(cls, "new", new)
        setattr(cls, "enqueue", enqueue)

        return cls

    return decorate
