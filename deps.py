import abc

from timesource import SystemTimeSource, TimeSource


class Dependencies:
    def GetTimeSource(self) -> TimeSource:
        return SystemTimeSource()
