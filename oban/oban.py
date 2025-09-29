from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Type, Union

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from . import query
from ._worker import worker
from .job import Job


@dataclass(frozen=True)
class Oban:
    connection: Union[Session, Engine]
    queues: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        for queue_name, limit in self.queues.items():
            if limit < 1:
                raise ValueError(f"Queue '{queue_name}' limit must be positive")

    def worker(self, **overrides) -> Callable[[Type], Type]:
        """Create a worker decorator for this Oban instance.

        The decorator adds worker functionality to a class, including job creation
        and enqueueing methods. The decorated class must implement a `perform` method.

        Args:
            **overrides: Configuration options for the worker (queue, priority, etc.)

        Returns:
            A decorator function that can be applied to worker classes

        Example:
            >>> oban_instance = Oban(queues={"default": 10, "mailers": 5})

            >>> @oban_instance.worker(queue="mailers", priority=1)
            ... class EmailWorker:
            ...     def perform(self, job):
            ...         # Send email logic here
            ...         print(f"Sending email: {job.args}")
            ...         return None

            >>> # Create a job without enqueueing
            >>> job = EmailWorker.new({"to": "user@example.com", "subject": "Hello"})
            >>> print(job.queue)  # "mailers"
            >>> print(job.priority)  # 1

            >>> # Create and enqueue a job
            >>> job = EmailWorker.enqueue(
            ...     {"to": "admin@example.com", "subject": "Alert"},
            ...     priority=5  # Override default priority
            ... )
            >>> print(job.priority)  # 5

        Note:
            The worker class must implement a `perform(self, job: Job) -> Result[Any]` method.
            If not implemented, a NotImplementedError will be raised when called.
        """
        return worker(oban=self, **overrides)

    def enqueue(self, job: Job) -> Job:
        conn = self._get_conn()

        return query.insert_job(conn, job)

    def _get_conn(self):
        if isinstance(self.connection, Session):
            return self.connection
        else:
            return self.connection.connect()
