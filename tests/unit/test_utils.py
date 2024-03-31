from datetime import timedelta

from src.utils import timedelta_new


def test_timedelta_days_float():
    assert timedelta_new(days=1.6357) == timedelta(days=1, seconds=54924, microseconds=48e4)


def test_timedelta_weeks_days_float():
    assert timedelta_new(weeks=1.5, days=1.6357) == timedelta(days=12, seconds=11724, microseconds=48e4)


def test_timedelta_weeks_days_microseconds_float():
    assert timedelta_new(weeks=1.5, days=1.6357, microseconds=8888888888888.5698432) == timedelta(
        days=115, seconds=1413, microseconds=368889
    )
