import datetime
from abc import ABC, abstractmethod


class TimeSource(ABC):
    @abstractmethod
    def now(self) -> datetime.datetime:
        pass


class SystemTimeSource(TimeSource):
    def now(self) -> datetime.datetime:
        return datetime.datetime.now().astimezone()
