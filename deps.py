from requester import Requester
from timesource import SystemTimeSource, TimeSource


class Dependencies:
    def get_time_source(self) -> TimeSource:
        return SystemTimeSource()

    def get_requester(self) -> Requester:
        return Requester()
