import datetime
from timesource import TimeSource
import re


def min_datetime_in_local_timezone(time_source: TimeSource) -> datetime.datetime:
    local_timezone = time_source.now().astimezone().tzinfo
    return datetime.datetime.min.replace(tzinfo=local_timezone)


def parse_utc_datetime(time_str: str) -> datetime.datetime:
    # ISO format supports using Z suffix for UTC but Python doesn't support this.
    time_str = time_str.replace("Z", "+00:00")
    # Remove millis, since some APIs return an unexpected number of digits.
    time_str = re.sub(r'\.[0-9]+', '', time_str)

    return datetime.datetime.fromisoformat(time_str)
