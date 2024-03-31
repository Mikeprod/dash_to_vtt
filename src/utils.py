import math
from datetime import timedelta
from typing import List, Union


def order_alphabetically(unsorted_list: List[str]) -> List[str]:
    """Order a list of segment names alphabetically.

    :param unsorted_list: list of strings to order
    :type unsorted_list: List[str]
    :return: list of strings ordered alphabetically
    :rtype: List[str]
    """
    return sorted(unsorted_list, key=lambda x: int(x.split("=")[-1].split("-")[-1].split(".")[0]))


def get_int(value: bytes) -> int:
    """Convert a bytes value to an integer.

    :param value: bytes value to convert
    :type value: bytes
    :return: integer value
    :rtype: int
    """
    return int(value.hex(), 16)


class timedelta_new(timedelta):
    """A subclass of timedelta that allows for float values in the constructor."""

    def __new__(cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        """Create a new timedelta object.

        :param days: number of days, defaults to 0
        :type days: int, optional
        :param seconds: number of seconds, defaults to 0
        :type seconds: int, optional
        :param microseconds: number of microseconds, defaults to 0
        :type microseconds: int, optional
        :param milliseconds: number of milliseconds, defaults to 0
        :type milliseconds: int, optional
        :param minutes: number of minutes, defaults to 0
        :type minutes: int, optional
        :param hours: number of hours, defaults to 0
        :type hours: int, optional
        :param weeks: number of weeks, defaults to 0
        :type weeks: int, optional
        :return: timedelta object
        :rtype: timedelta
        """
        # Normalize everything to days, seconds, microseconds.
        _days = days + weeks * 7
        _seconds = seconds + minutes * 60 + hours * 3600
        _microseconds = microseconds + milliseconds * 1000

        # Get rid of all fractions, and normalize s and us.
        d_days, d_seconds, d_frac_seconds = cls._convert_days_to_days_n_seconds(_days)
        s_days, s_seconds, s_frac_seconds = cls._convert_seconds_to_days_n_seconds(_seconds)

        if abs(d_frac_seconds + s_frac_seconds) > 2.0:
            raise AssertionError("Decimal values of seconds should not be greater than 2.0")

        u_seconds = (s_frac_seconds + d_frac_seconds) * 1e6
        if abs(u_seconds) >= 2.1e6:  # exact value not critical
            raise AssertionError("Microseconds should not be greater than 2.1e6")
        u_days, u_seconds, u_frac_seconds = cls._convert_microseconds_to_days_n_seconds(_microseconds)
        if (d_seconds + s_seconds + u_seconds) >= 3 * 24 * 3600:
            raise AssertionError("Seconds should not be greater than 3 * 24 * 3600")
        if round(u_seconds + u_frac_seconds) >= 3.1e6:
            raise AssertionError("Microseconds should not be greater than 3.1e6")

        # Just a bit of carrying possible for microseconds and seconds.
        adjusted_seconds, output_u_seconds = divmod(u_seconds + u_frac_seconds, 1000000)
        adjusted_days, output_seconds = divmod(d_seconds + s_seconds + u_seconds + adjusted_seconds, 24 * 3600)
        output_days = int(d_days + s_days + adjusted_days)

        # Checking that the last values are within the expected range
        if not 0 <= int(output_seconds) < 24 * 3600:
            raise AssertionError("Seconds should be an integer and between 0 and 24 * 3600")
        if not 0 <= int(output_u_seconds) < 1000000:
            raise AssertionError("Microseconds should be an integer and between 0 and 1000000")

        if abs(output_days) > 999999999:
            raise OverflowError(f"timedelta # of days is too large: {output_days}")

        self = super().__new__(cls, days, seconds, microseconds, milliseconds, minutes, hours, weeks)
        self._days = output_days
        self._seconds = int(output_seconds)
        self._microseconds = int(output_u_seconds)
        self._hashcode = -1
        return self

    @classmethod
    def _convert_days_to_days_n_seconds(cls, days: Union[int, float]) -> tuple[int, int, float]:
        seconds_decimals = 0.0
        full_seconds = 0
        full_days = days
        if isinstance(days, float):
            days_decimals, full_days = math.modf(days)
            seconds_decimals, full_seconds = math.modf(days_decimals * (24.0 * 3600.0))
        return int(full_days), int(full_seconds), seconds_decimals

    @classmethod
    def _convert_seconds_to_days_n_seconds(cls, seconds: Union[int, float]) -> tuple[int, int, float]:
        seconds_full = seconds
        second_frac = 0.0
        if isinstance(seconds, float):
            second_frac, seconds_full = math.modf(seconds)
        # Divide the seconds to get the days and seconds
        days, remaining_seconds = divmod(seconds_full, 24 * 3600)
        return int(days), int(seconds_full + remaining_seconds), second_frac

    @classmethod
    def _convert_microseconds_to_days_n_seconds(cls, microseconds: Union[int, float]) -> tuple[int, int, float]:
        if isinstance(microseconds, float):
            seconds, u_sec = divmod(microseconds, 1000000)
            days, full_seconds = divmod(seconds, 24 * 3600)
        else:
            seconds, u_sec = divmod(int(microseconds), 1000000)
            days, full_seconds = divmod(seconds, 24 * 3600)
        return int(days), int(full_seconds), u_sec

    def __str__(self):
        """Return a string representation of the timedelta."""
        mm, ss = divmod(self.seconds, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d:%02d" % (hh, mm, ss)
        return s + ".%03d" % (self.microseconds // 1000)
