from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .job import Job
    from .leader import Leader
    from ._query import Query

DOW_DICT = {
    "MON": "1",
    "TUE": "2",
    "WED": "3",
    "THU": "4",
    "FRI": "5",
    "SAT": "6",
    "SUN": "7",
}

MON_DICT = {
    "JAN": "1",
    "FEB": "2",
    "MAR": "3",
    "APR": "4",
    "MAY": "5",
    "JUN": "6",
    "JUL": "7",
    "AUG": "8",
    "SEP": "9",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}

MIN_SET = frozenset(range(0, 60))
HRS_SET = frozenset(range(0, 24))
DAY_SET = frozenset(range(1, 32))
MON_SET = frozenset(range(1, 13))
DOW_SET = frozenset(range(1, 8))

NICKNAMES = {
    "@annually": "0 0 1 1 *",
    "@yearly": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@midnight": "0 0 * * *",
    "@daily": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# TODO: Type this, and get a real structure.
_table = []


def _trans_field(input: str, mapper: dict) -> str:
    for val in mapper:
        if val in input:
            input = input.replace(val, mapper[val])

    return input


def _parse_field(field: str, all: set) -> set(int):
    parsed = set()

    for part in re.split(r"\s*,\s*", field):
        parsed.update(_parse_part(part, all))

    if not parsed.issubset(all):
        raise ValueError(f"field {field} is out of range: {all}")

    return parsed


def _parse_part(part: str, all: set) -> set(int):
    if part == "*":
        return all
    elif re.match(r"^\d+$", part):
        return _parse_literal(part)
    elif re.match(r"^\*\/[1-9]\d?$", part):
        return _parse_step(part, all)
    elif re.match(r"^\d+(\-\d+)?\/[1-9]\d?$", part):
        return _parse_range_step(part, all)
    elif re.match(r"^\d+\-\d+$", part):
        return _parse_range(part, all)
    else:
        raise ValueError(f"unrecognized expression: {part}")


def _parse_literal(part: str) -> set(int):
    return {int(part)}


def _parse_step(part: str, all: set) -> set(int):
    step = int(part.replace("*/", ""))

    return set(range(min(all), max(all) + 1, step))


def _parse_range_step(part: str, all: set) -> set(int):
    (sub_range, part) = part.split("/")

    return _parse_step(part, _parse_range(sub_range, all))


def _parse_range(part: str, all: set) -> set(int):
    match part.split("-"):
        case [rmin]:
            rmin = int(rmin)

            return set(range(rmin, max(all) + 1))
        case [rmin, rmax]:
            rmin = int(rmin)
            rmax = int(rmax)

            if rmin > rmax:
                raise ValueError(
                    f"min of range ({rmin}) must be less than or equal to max"
                )

            return set(range(rmin, rmax + 1))
        case _:
            raise ValueError(f"unrecognized range: {part}")


@dataclass(slots=True, frozen=True)
class Expression:
    input: str
    minutes: set
    hours: set
    days: set
    months: set
    weekdays: set

    @classmethod
    def parse(cls, input: str) -> Expression:
        """Parse a crontab expression into an expression object"""
        if input in NICKNAMES:
            input = NICKNAMES[input]

        match re.split(r"\s+", input):
            case [mip, hrp, dap, mop, wdp]:
                mop = _trans_field(mop, MON_DICT)
                wdp = _trans_field(wdp, DOW_DICT)

                return cls(
                    input=input,
                    minutes=_parse_field(mip, MIN_SET),
                    hours=_parse_field(hrp, HRS_SET),
                    days=_parse_field(dap, DAY_SET),
                    months=_parse_field(mop, MON_SET),
                    weekdays=_parse_field(wdp, DOW_SET),
                )
            case _:
                raise ValueError(f"incorrect number of fields: {input}")

    def is_now(self, time: None | datetime = None) -> bool:
        """Check whether a cron expression matches the current date and time."""
        time = time or datetime.now(timezone.utc)

        return (
            time.month in self.months
            and time.isoweekday() in self.weekdays
            and time.day in self.days
            and time.hour in self.hours
            and time.minute in self.minutes
        )


# TODO: Look into a better name than just "Cron", it's not an action. What about naming this scheduler
# instead?
class Cron:
    def __init__(
        self,
        *,
        leader: Leader,
        query: Query,
    ) -> None:
        self._leader = leader
        self._query = query

        self._loop_task = None

    async def start(self) -> None:
        self._loop_task = asyncio.create_task(self._loop(), name="oban-cron")

    async def stop(self) -> None:
        self._loop_task.cancel()

        try:
            await self._loop_task
        except asyncio.CancelledError:
            pass

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._time_to_next_minute())

                if self._leader.is_leader:
                    await self._evaluate()
            except asyncio.CancelledError:
                break

    async def _evaluate(self) -> None:
        jobs = [self._build(*entry) for entry in _table if entry[0].is_now]

        # TODO: Actually enqueue them. We want to use `oban.enqueue_many` to get the
        # notifications.
        print(jobs)

    # TODO: Figure out what we're actually using to enqueue here
    def _build(expr, thingy, opts) -> Job:
        pass

    def _time_to_next_minute(self, time: None | datetime = None) -> float:
        time = time or datetime.now(timezone.utc)
        next_minute = (time + timedelta(minutes=1)).replace(second=0, microsecond=0)

        return (next_minute - time).total_seconds()
