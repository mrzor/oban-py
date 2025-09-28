from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .types import JobState


@dataclass(slots=True, frozen=True)
class Job:
    worker: str
    id: int | None = None
    state: JobState = "available"
    queue: str = "default"
    attempt: int = 0
    max_attempts: int = 20
    priority: int = 0
    args: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    attempted_by: tuple[str, ...] = ()
    scheduled_at: datetime | None = None
    attempted_at: datetime | None = None
    completed_at: datetime | None = None
    discarded_at: datetime | None = None
    cancelled_at: datetime | None = None
