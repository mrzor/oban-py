from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from psycopg_pool import AsyncConnectionPool


@runtime_checkable
class Driver(Protocol):
    """Protocol for database drivers."""

    def connection(self) -> Any:
        """Return an async context manager that yields a connection.

        Returns:
            An async context manager that yields a connection object.
        """
        ...

    @property
    def dsn(self) -> str:
        """Return the connection string for creating new connections.

        Returns:
            Connection string with credentials intact.
        """
        ...


class PsycopgPoolDriver:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    def connection(self) -> Any:
        return self._pool.connection()

    @property
    def dsn(self) -> str:
        return self._pool.conninfo


def wrap_pool(pool: Any) -> Driver:
    try:
        from psycopg_pool import AsyncConnectionPool

        if isinstance(pool, AsyncConnectionPool):
            return PsycopgPoolDriver(pool)
    except ImportError:
        pass

    raise TypeError(f"Unsupported pool provided: {type(pool).__name__}")
