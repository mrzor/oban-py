import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
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
    inserted_at: datetime | None = None
    attempted_at: datetime | None = None
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    discarded_at: datetime | None = None
    scheduled_at: datetime | None = None

    def to_dict(self) -> dict:
        data = asdict(self)

        data["args"] = json.dumps(data["args"])
        data["meta"] = json.dumps(data["meta"])
        data["errors"] = json.dumps(list(data["errors"]))
        data["tags"] = json.dumps(list(data["tags"]))
        data["attempted_by"] = list(data["attempted_by"])

        return data
