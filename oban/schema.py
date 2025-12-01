"""Database schema installation for Oban."""

from typing import Any

from ._extensions import use_ext
from ._query import Query


def _noop_sql(prefix: str) -> str:
    return ""


def install_sql(prefix: str = "public") -> str:
    """Get the SQL for installing Oban.

    Returns the raw SQL statements for creating Oban types, tables, and indexes.
    This is intended for integration with migration frameworks like Django or Alembic.

    Args:
        prefix: PostgreSQL schema where Oban tables will be located (default: "public")

    Returns:
        SQL string for schema installation

    Example (Alembic):
        >>> from alembic import op
        >>> from oban.schema import install_sql
        >>>
        >>> def upgrade():
        ...     op.execute(install_sql())

    Example (Django):
        >>> from django.db import migrations
        >>> from oban.schema import install_sql
        >>>
        >>> class Migration(migrations.Migration):
        ...     operations = [
        ...         migrations.RunSQL(install_sql()),
        ...     ]
    """
    base_sql = Query._load_file("install.sql", prefix)
    xtra_sql = use_ext("schema.install_sql", _noop_sql, prefix)

    return f"{base_sql}\n{xtra_sql}"


def uninstall_sql(prefix: str = "public") -> str:
    """Get the SQL for uninstalling Oban.

    Returns the raw SQL statements for dropping Oban tables and types.
    Useful for integration with migration frameworks like Alembic or Django.

    Args:
        prefix: PostgreSQL schema where Oban tables are located (default: "public")

    Returns:
        SQL string for schema uninstallation

    Example (Alembic):
        >>> from alembic import op
        >>> from oban.schema import uninstall_sql
        >>>
        >>> def downgrade():
        ...     op.execute(uninstall_sql())

    Example (Django):
        >>> from django.db import migrations
        >>> from oban.schema import uninstall_sql
        >>>
        >>> class Migration(migrations.Migration):
        ...     operations = [
        ...         migrations.RunSQL(uninstall_sql()),
        ...     ]
    """
    return Query._load_file("uninstall.sql", prefix)


def upgrade_sql(prefix: str = "public") -> str:
    """Get the SQL for upgrading Oban.

    Returns the raw SQL statements for upgrading Oban schema extensions.
    All statements are idempotent and safe to run multiple times.

    Args:
        prefix: PostgreSQL schema where Oban tables are located (default: "public")

    Returns:
        SQL string for schema upgrade
    """
    return use_ext("schema.upgrade_sql", _noop_sql, prefix)


async def install(pool: Any, prefix: str = "public") -> None:
    """Install Oban in the specified database.

    Creates all necessary types, tables, and indexes for Oban to function. The
    installation is wrapped in a DDL transaction to ensure the operation is
    atomic.

    Args:
        pool: A database connection pool (e.g., AsyncConnectionPool)
        prefix: PostgreSQL schema where Oban tables will be located (default: "public")

    Example:
        >>> from psycopg_pool import AsyncConnectionPool
        >>> from oban.schema import install
        >>>
        >>> pool = AsyncConnectionPool(conninfo=DATABASE_URL, open=False)
        >>> await pool.open()
        >>> await install(pool)
    """
    async with pool.connection() as conn:
        await conn.execute(install_sql(prefix))


async def upgrade(pool: Any, prefix: str = "public") -> None:
    """Upgrade Oban schema extensions in the specified database.

    Applies any schema upgrades from extensions. All operations are idempotent
    and safe to run multiple times.

    Args:
        pool: A database connection pool (e.g., AsyncConnectionPool)
        prefix: PostgreSQL schema where Oban tables are located (default: "public")

    Example:
        >>> from psycopg_pool import AsyncConnectionPool
        >>> from oban.schema import upgrade
        >>>
        >>> pool = AsyncConnectionPool(conninfo=DATABASE_URL, open=False)
        >>> await pool.open()
        >>> await upgrade(pool)
    """
    async with pool.connection() as conn:
        await conn.execute(upgrade_sql(prefix))


async def uninstall(pool: Any, prefix: str = "public") -> None:
    """Uninstall Oban from the specified database.

    Drops all Oban tables and types. The uninstallation is wrapped in a DDL
    transaction to ensure the operation is atomic.

    Args:
        pool: A database connection pool (e.g., AsyncConnectionPool)
        prefix: PostgreSQL schema where Oban tables are located (default: "public")

    Example:
        >>> from psycopg_pool import AsyncConnectionPool
        >>> from oban.schema import uninstall
        >>>
        >>> pool = AsyncConnectionPool(conninfo=DATABASE_URL, open=False)
        >>> await pool.open()
        >>> await uninstall(pool)
    """
    async with pool.connection() as conn:
        await conn.execute(uninstall_sql(prefix))
