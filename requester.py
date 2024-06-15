import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
from typing import Dict, List, Optional, Protocol

import requests
from croniter import croniter

from timesource import TimeSource

_LOG_REQUESTS = False


class ParseCallback(Protocol):
    def __call__(self, response: requests.models.Response) -> bool:
        pass


class ErrorCallback(Protocol):
    def __call__(self, response: Optional[requests.models.Response]) -> None:
        pass


class UrlCallback(Protocol):
    def __call__(self) -> Optional[str]:
        pass


@dataclass
class Endpoint:
    name: str
    parse_callback: ParseCallback
    error_callback: ErrorCallback
    url: Optional[str] = None
    url_callback: Optional[UrlCallback] = None
    refresh_interval: Optional[datetime.timedelta] = None
    refresh_schedule: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure that only one of url or url_callback is set.
        if self.url is None and self.url_callback is None:
            raise TypeError("Either url or url_callback must be specified.")
        if self.url is not None and self.url_callback is not None:
            raise TypeError(
                "One one of url or url_callback should be specified.")

        # Ensure that only one of refresh_interval or refresh_schedule is set.
        if self.refresh_interval is None and self.refresh_schedule is None:
            raise TypeError(
                "Either refresh_interval or refresh_schedule must be specified.")
        if self.refresh_interval is not None and self.refresh_schedule is not None:
            raise TypeError(
                "Only one of refresh_interval or refresh_schedule should be specified.")

        # If refresh_schedule is given, it must be a valid cron expression.
        if self.refresh_schedule is not None:
            if not croniter.is_valid(self.refresh_schedule):
                raise TypeError("Invalid refresh_schedule")

    def get_url(self) -> Optional[str]:
        if self.url is not None:
            return self.url
        elif self.url_callback is not None:
            return self.url_callback()
        else:
            return None


class Requester(ABC):
    @abstractmethod
    def add_endpoint(self, endpoint: Endpoint) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class RequesterThread:
    endpoint: Endpoint
    time_source: TimeSource
    failures_without_success: int
    timer: threading.Timer

    def __init__(self, endpoint: Endpoint, time_source: TimeSource) -> None:
        self.endpoint = endpoint
        self.time_source = time_source
        self.failures_without_success = 0

    def start(self) -> None:
        logging.debug("Starting requests to %s", self.endpoint.name)
        self._request_with_retries()

    def stop(self) -> None:
        if self.timer is not None:
            self.timer.cancel()

    def _request_with_retries(self) -> None:
        url = self.endpoint.get_url()
        # Missing URL may indicate that there is temporarily nothing to request.
        if url is None:
            self._schedule_next_request()
            return

        try:
            response = requests.get(url, headers=self.endpoint.headers)
        except Exception as e:
            self.failures_without_success += 1
            self.endpoint.error_callback(None)
            logging.warning("Exception making request for endpoint %s (failures: %d). Url: %s, exception: %s",
                            self.endpoint.name, self.failures_without_success, url, e)
            self._schedule_retry()
            return

        self._log_to_file(response)

        if response.status_code >= 300:
            self.failures_without_success += 1
            self.endpoint.error_callback(response)
            logging.warning("Non-2xx response %d from endpoint %s (failures: %d). Url: %s, response: %s",
                            response.status_code, self.endpoint.name, self.failures_without_success, url, response.content)
            self._schedule_retry()
            return

        try:
            parse_success = self.endpoint.parse_callback(response)
        except Exception as e:
            self.failures_without_success += 1
            logging.warning("Exception parsing response from endpoint %s (failures: %d). Exception: %s", self.endpoint.name, self.failures_without_success, e)
            self._schedule_retry()
            return

        if parse_success:
            self.failures_without_success = 0
            self._schedule_next_request()
        else:
            self.failures_without_success += 1
            self._schedule_retry()

    def _schedule_retry(self) -> None:
        if self.failures_without_success == 1:
            self.timer = threading.Timer(1, self._request_with_retries)
            self.timer.start()
        elif self.failures_without_success == 2:
            self.timer = threading.Timer(30, self._request_with_retries)
            self.timer.start()
        else:
            self._schedule_next_request()

    def _schedule_next_request(self) -> None:
        if self.endpoint.refresh_interval is not None:
            logging.debug("Scheduling next request in %d seconds",
                          self.endpoint.refresh_interval.seconds)
            self.timer = threading.Timer(
                self.endpoint.refresh_interval.seconds, self._request_with_retries)
            self.timer.start()
        elif self.endpoint.refresh_schedule is not None:
            next = croniter(self.endpoint.refresh_schedule,
                            self.time_source.now()).get_next(datetime.datetime)
            time_until_next = next - self.time_source.now()
            logging.debug(
                "Scheduling next request in %d seconds (at %s)", time_until_next.seconds, next)
            self.timer = threading.Timer(
                time_until_next.seconds, self._request_with_retries)
            self.timer.start()

    def _log_to_file(self, content: requests.models.Response) -> None:
        if _LOG_REQUESTS:
            filename = "debug/%d_%s.txt" % (int(time.time()),
                                            self.endpoint.name)
            with open(filename, 'w') as f:
                f.write(content.content.decode('utf-8'))


class HttpRequester(Requester):
    time_source: TimeSource
    configured_endpoints: List[Endpoint]
    threads: List[RequesterThread]

    def __init__(self, time_source: TimeSource) -> None:
        self.time_source = time_source
        self.configured_endpoints = []
        self.threads = []

    def add_endpoint(self, endpoint: Endpoint) -> None:
        self.configured_endpoints.append(endpoint)

    def start(self) -> None:
        self.threads = [RequesterThread(endpoint, self.time_source)
                        for endpoint in self.configured_endpoints]
        for t in self.threads:
            t.start()

    def stop(self) -> None:
        for t in self.threads:
            t.stop()
        self.threads = []
