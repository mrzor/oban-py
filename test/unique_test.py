from datetime import datetime

from oban import Job
from oban._unique import with_uniq_meta


def utc(iso_string):
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def with_uniq(**params):
    return with_uniq_meta(Job.new(**params))


class TestWithUniqMeta:
    def test_no_unique_returns_job_unchanged(self):
        assert "uniq" not in with_uniq(worker="Worker").meta

    def test_unique_true_adds_metadata(self):
        job = with_uniq(
            worker="Worker", args={"id": 1}, meta={"custom": True}, unique=True
        )

        assert job.meta["uniq"]
        assert job.meta["custom"]
        assert isinstance(job.meta["uniq_bmp"], list)
        assert isinstance(job.meta["uniq_key"], str)

    def test_unique_group_injects_bitmap(self):
        job = with_uniq(worker="Worker", unique={"group": "scheduled"})

        assert job.meta["uniq_bmp"] == [0]

    def test_same_args_produce_same_key(self):
        job_1 = with_uniq(worker="Worker", args={"id": 1}, unique=True)
        job_2 = with_uniq(worker="Worker", args={"id": 1}, unique=True)

        assert job_1.meta["uniq_key"] == job_2.meta["uniq_key"]

    def test_different_args_produce_different_keys(self):
        job_1 = with_uniq(worker="Worker", args={"id": 1}, unique=True)
        job_2 = with_uniq(worker="Worker", args={"id": 2}, unique=True)

        assert job_1.meta["uniq_key"] != job_2.meta["uniq_key"]

    def test_different_workers_produce_different_keys(self):
        job_1 = with_uniq(worker="A", args={"id": 1}, unique=True)
        job_2 = with_uniq(worker="B", args={"id": 1}, unique=True)

        assert job_1.meta["uniq_key"] != job_2.meta["uniq_key"]

    def test_different_queues_produce_different_keys(self):
        job_1 = with_uniq(worker="Worker", queue="default", args={"id": 1}, unique=True)
        job_2 = with_uniq(worker="Worker", queue="other", args={"id": 1}, unique=True)

        assert job_1.meta["uniq_key"] != job_2.meta["uniq_key"]

    def test_fields_option_only_args(self):
        job_1 = with_uniq(worker="A", args={"id": 1}, unique={"fields": ["args"]})
        job_2 = with_uniq(worker="B", args={"id": 1}, unique={"fields": ["args"]})

        assert job_1.meta["uniq_key"] == job_2.meta["uniq_key"]

    def test_keys_option_filters_args(self):
        unique = {"fields": ["args"], "keys": ["id"]}

        job_1 = with_uniq(worker="Worker", args={"id": 1, "name": "Foo"}, unique=unique)
        job_2 = with_uniq(worker="Worker", args={"id": 1, "name": "Bar"}, unique=unique)
        job_3 = with_uniq(worker="Worker", args={"id": 2, "name": "Bar"}, unique=unique)

        assert job_1.meta["uniq_key"] == job_2.meta["uniq_key"]
        assert job_1.meta["uniq_key"] != job_3.meta["uniq_key"]

    def test_preserves_existing_meta(self):
        result = with_uniq(
            worker="Worker",
            args={"id": 1},
            meta={"custom": "value"},
            unique=True,
        )

        assert result.meta["custom"] == "value"
        assert result.meta["uniq"]
        assert "uniq_key" in result.meta

    def test_period_includes_timestamp_in_key(self):
        job_1 = with_uniq(
            worker="Worker",
            unique={"period": 60},
            scheduled_at=utc("2025-01-01T12:00:00Z"),
        )

        job_2 = with_uniq(
            worker="Worker",
            unique={"period": 60},
            scheduled_at=utc("2025-01-01T12:00:59"),
        )

        job_3 = with_uniq(
            worker="Worker",
            unique={"period": 60},
            scheduled_at=utc("2025-01-01T12:01:00Z"),
        )

        assert job_1.meta["uniq_key"] == job_2.meta["uniq_key"]
        assert job_2.meta["uniq_key"] != job_3.meta["uniq_key"]
