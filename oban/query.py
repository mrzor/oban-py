from dataclasses import replace
from functools import lru_cache
from importlib.resources import files
from sqlalchemy import text

from .job import Job


@lru_cache(maxsize=None)
def _load_file(path: str) -> str:
    file = files("oban.queries").joinpath(path).read_text(encoding="utf-8")

    return text(file)


def insert_job(conn, job: Job):
    stmt = _load_file("insert_job.sql")
    data = job.to_dict()

    row = conn.execute(stmt, data).first()

    return replace(job, **row._asdict())
