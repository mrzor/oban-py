import pytest
import random

from datetime import datetime, timezone

from oban.cron import Expression, Scheduler


class TestExpressionParse:
    def test_parsing_simple_expressions(self):
        assert isinstance(Expression.parse("* * * * *"), Expression)

        with pytest.raises(ValueError, match="incorrect number of fields"):
            Expression.parse("* * *")

    def test_parsing_nicknames(self):
        assert {0} == Expression.parse("@hourly").minutes
        assert {0} == Expression.parse("@daily").hours
        assert {1} == Expression.parse("@monthly").days

    def test_parsing_month_aliases(self):
        assert {1} == Expression.parse("* * * JAN *").months
        assert {6, 7} == Expression.parse("* * * JUN,JUL *").months

    def test_parsing_weekday_aliases(self):
        assert {1} == Expression.parse("* * * * MON").weekdays
        assert {2, 7} == Expression.parse("* * * * SUN,TUE").weekdays

    def test_parsing_upper_bounds(self):
        assert Expression.parse("59 23 31 12 7")

    def test_parsing_out_of_bounds(self):
        inputs = [
            "60 * * * *",
            "* 24 * * *",
            "* * 32 * *",
            "* * * 13 *",
            "* * * * 0",
        ]

        for input in inputs:
            with pytest.raises(ValueError, match="out of range"):
                Expression.parse(input)

    def test_parsing_unrecognized_expressions(self):
        inputs = [
            "*/0 * * * *",
            "ONE * * * *",
            "* * * jan *",
            "* * * * sun",
        ]

        for input in inputs:
            with pytest.raises(ValueError, match="unrecognized expression"):
                Expression.parse(input)

    def test_step_ranges_are_calculated_from_lowest_value(self):
        assert {0, 12} == Expression.parse("* 0/12 * * *").hours
        assert {1, 8, 15, 22} == Expression.parse("* 1/7 * * *").hours
        assert {1, 8} == Expression.parse("* 1-14/7 * * *").hours

    @pytest.mark.parametrize("seed", range(1, 20))
    def test_parsing_valid_expression_combinations(self, seed):
        random.seed(seed)

        def wildcard(_min_val, _max_val):
            return "*"

        def literal(min_val, max_val):
            return str(random.randint(min_val, max_val))

        def step_from_literal(min_val, max_val):
            base = random.randint(min_val, max_val)
            step = random.randint(2, max(2, (max_val - min_val) // 2))

            return f"{base}/{step}"

        def step_from_wildcard(min_val, max_val):
            step = random.randint(2, max(2, max_val - min_val))

            return f"*/{step}"

        def range_expr(min_val, max_val):
            start = random.randint(min_val, max_val - 1)
            end = random.randint(start + 1, max_val)

            return f"{start}-{end}"

        def range_with_step(min_val, max_val):
            start = random.randint(min_val, max_val - 2)
            end = random.randint(start + 2, max_val)
            step = 2

            return f"{start}-{end}/{step}"

        def list_expr(min_val, max_val):
            count = random.randint(2, min(5, max_val - min_val + 1))
            values = random.sample(range(min_val, max_val + 1), count)

            return ",".join(str(val) for val in sorted(values))

        generators = {
            "minute": (0, 59),
            "hour": (0, 23),
            "day": (1, 31),
            "month": (1, 12),
            "weekday": (1, 7),
        }

        patterns = [
            wildcard,
            literal,
            step_from_literal,
            step_from_wildcard,
            range_expr,
            range_with_step,
            list_expr,
        ]

        picks = random.sample(patterns, 5)
        parts = []

        for gen, (_field, (min_val, max_val)) in zip(picks, generators.items()):
            parts.append(gen(min_val, max_val))

        expression = " ".join(parts)

        assert isinstance(Expression.parse(expression), Expression)


class TestExpressionIsNow:
    @pytest.mark.parametrize("seed", range(1, 10))
    def test_matching_literal_values(self, seed):
        random.seed(seed)

        min = random.randint(1, 59)
        hrs = random.randint(1, 23)
        day = random.randint(2, 28)
        mon = random.randint(2, 12)

        time = datetime.now().replace(month=mon, day=day, hour=hrs, minute=min)
        expr = Expression.parse(f"{min} {hrs} {day} {mon} *")

        assert expr.is_now(time)
        assert not expr.is_now(time.replace(minute=min - 1))
        assert not expr.is_now(time.replace(hour=hrs - 1))
        assert not expr.is_now(time.replace(day=day - 1))
        assert not expr.is_now(time.replace(month=mon - 1))

    def test_matching_literal_weekdays(self):
        sunday = datetime.now().replace(year=2025, month=10, day=12)

        assert Expression.parse("* * * * SUN").is_now(sunday)


class TestSchedulerTimeToNextMinute:
    @pytest.fixture
    def cron(self):
        return Scheduler(leader=None, query=None)

    def time_to_next_minute(self, cron, *, hour=12, minute=34, second=0, microsecond=0):
        time = datetime.now(timezone.utc).replace(
            hour=hour, minute=minute, second=second, microsecond=microsecond
        )

        return cron._time_to_next_minute(time)

    def test_seconds_until_next_minute(self, cron):
        assert self.time_to_next_minute(cron, second=0) == 60.0
        assert self.time_to_next_minute(cron, second=1) == 59.0
        assert self.time_to_next_minute(cron, second=30) == 30.0
        assert self.time_to_next_minute(cron, second=59) == 1.0

    def test_at_end_of_hour(self, cron):
        assert self.time_to_next_minute(cron, minute=59, second=45) == 15.0

    def test_at_end_of_day(self, cron):
        assert self.time_to_next_minute(cron, hour=23, minute=59, second=30) == 30.0

    @pytest.mark.parametrize("second", [0, 15, 30, 45, 59])
    @pytest.mark.parametrize("micro", [0, 500000, 999999])
    def test_always_returns_positive_value_in_range(self, cron, second, micro):
        result = self.time_to_next_minute(cron, second=second, microsecond=micro)

        assert 0 < result <= 60.0
