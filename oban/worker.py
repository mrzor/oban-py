from typing import Any, Protocol, runtime_checkable
from dataclasses import fields

from .job import Job
from .types import Result


@runtime_checkable
class Worker(Protocol):
    """Your workers must implement this."""

    def perform(self, job: Job) -> Result[Any]: ...


def worker(**overrides):
    """
    Decorate a class to make it a viable worker.

    Injects:
      - class attribute: _opts
      - classmethod: new(args: dict, **overrides) -> Job
    """

    def decorate(cls: type) -> type:
        setattr(cls, "_opts", overrides)

        # This is perfectly idiomatic when you want a semantic constructor that returns something other than the class itself.
        # Inject .new(args, **overrides) -> Job
        @classmethod
        def new(cls, args: dict[str, Any], /, **overrides) -> Job:
            cfg = {**cls._opts, **overrides}
            return Job(worker=cls.__name__, args=args, **cfg)

        setattr(cls, "new", new)

        return cls

    return decorate
