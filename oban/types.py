from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

T = TypeVar("T")


class JobState(StrEnum):
    """Represents the lifecycle state of a job.

    - AVAILABLE: ready to be executed
    - SCHEDULED: scheduled to run in the future
    - EXECUTING: currently executing
    - RETRYABLE: failed but will be retried
    - COMPLETED: successfully finished
    - DISCARDED: exceeded max attempts
    - CANCELLED: explicitly cancelled
    """

    AVAILABLE = "available"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    RETRYABLE = "retryable"
    COMPLETED = "completed"
    DISCARDED = "discarded"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Snooze:
    seconds: int


@dataclass(frozen=True)
class Cancel:
    reason: str


type Result[T] = Snooze | Cancel | None
