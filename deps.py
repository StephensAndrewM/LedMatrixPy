from timesource import SystemTimeSource, TimeSource


class Dependencies:
    def get_time_source(self) -> TimeSource:
        return SystemTimeSource()
