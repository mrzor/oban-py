import pytest
import random

from datetime import datetime

from oban.cron import Expression


class TestExpressionParse:
    def test_parsing_simple_expressions(self):
        assert isinstance(Expression.parse("* * * * *"), Expression)

        with pytest.raises(ValueError, match="incorrect number of fields"):
            Expression.parse("* * *")

    def test_parsing_nicknames(self):
        assert "0 * * * *" == Expression.parse("@hourly").input
        assert "0 0 * * *" == Expression.parse("@daily").input
        assert "0 0 1 * *" == Expression.parse("@monthly").input

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


class TestExpressionIsNow:
    @pytest.mark.parametrize("seed", range(1, 10))
    def test_matching_literal_values(self, seed):
        random.seed(seed)

        min = random.randint(1, 59)
        hor = random.randint(1, 23)
        day = random.randint(2, 28)
        mon = random.randint(2, 12)

        time = datetime.now().replace(month=mon, day=day, hour=hor, minute=min)
        expr = Expression.parse(f"{min} {hor} {day} {mon} *")

        assert expr.is_now(time)
        assert not expr.is_now(time.replace(minute=min - 1))
        assert not expr.is_now(time.replace(hour=hor - 1))
        assert not expr.is_now(time.replace(day=day - 1))
        assert not expr.is_now(time.replace(month=mon - 1))

    def test_matching_literal_weekdays(self):
        sunday = datetime.now().replace(year=2025, month=10, day=12)

        assert Expression.parse("* * * * SUN").is_now(sunday)
