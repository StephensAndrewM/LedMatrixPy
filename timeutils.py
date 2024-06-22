import datetime
from timesource import TimeSource


def min_datetime_in_local_timezone(time_source: TimeSource) -> datetime.datetime:
    local_timezone = time_source.now().astimezone().tzinfo
    return datetime.datetime.min.replace(tzinfo=local_timezone)

def parse_utc_datetime(time_str: str) -> datetime.datetime:
    # ISO format supports using Z suffix for UTC but Python doesn't support this.
    return datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00"))