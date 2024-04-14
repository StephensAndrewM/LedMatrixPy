from requester import HttpRequester, Requester
from timesource import SystemTimeSource, TimeSource


class Dependencies:
    _requester: Requester
    _time_source: TimeSource

    def __init__(self) -> None:
        self._time_source = SystemTimeSource()
        self._requester = HttpRequester(self._time_source)

    def get_time_source(self) -> TimeSource:
        return self._time_source

    def get_requester(self) -> Requester:
        return self._requester
