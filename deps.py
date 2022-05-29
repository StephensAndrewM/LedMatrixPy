import abc

from timesource import TimeSource, SystemTimeSource

class Dependencies:
    def GetTimeSource(self) -> TimeSource:
        return SystemTimeSource()