import pytest

from test.session import create_session

from oban import Oban


class TestObanIntegration:
    @classmethod
    def setup_class(cls):
        cls.session = create_session()

    @classmethod
    def teardown_class(cls):
        cls.session.rollback()
        cls.session.close()

    def test_inserting_and_executing_jobs(self):
        oban = Oban(connection=self.session, queues={"default": 10})

        # TODO: Use oban.start() when we have something that actually works

        @oban.worker()
        class Worker:
            def perform(self, job):
                match job.args:
                    case {"act": "er"}:
                        raise RuntimeError("this failed")
                    case {"act": "ca"}:
                        return Cancel("no reason")
                    case {"act": "sn"}:
                        return Snooze(1)
                    case _:
                        return None

        Worker.enqueue({"act": "ok", "ref": 1})
        Worker.enqueue({"act": "er", "ref": 2})
        Worker.enqueue({"act": "ca", "ref": 3})
        Worker.enqueue({"act": "sn", "ref": 4})
