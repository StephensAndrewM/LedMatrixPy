from abc import ABC, abstractmethod
import logging
import threading
from dataclasses import dataclass
from datetime import timedelta
import time
from typing import Dict, List, Optional, Protocol

import requests


_LOG_REQUESTS = False


class ParseCallback(Protocol):
    def __call__(self, response: requests.models.Response) -> bool:
        pass


class ErrorCallback(Protocol):
    def __call__(self, response: Optional[requests.models.Response]) -> None:
        pass


@dataclass
class Endpoint:
    url: str
    name: str
    refresh_interval: timedelta
    parse_callback: ParseCallback
    error_callback: ErrorCallback
    headers: Dict[str, str]


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
    timer: threading.Timer
    failures_without_success: int

    def __init__(self, endpoint: Endpoint) -> None:
        self.endpoint = endpoint
        self.failures_without_success = 0

    def start(self) -> None:
        logging.debug("Starting requests to %s", self.endpoint.name)
        self.request_with_retries()

    def stop(self) -> None:
        if self.timer is not None:
            self.timer.cancel()

    def request_with_retries(self) -> None:
        try:
            response = requests.get(
                self.endpoint.url, headers=self.endpoint.headers)
        except Exception as e:
            self.failures_without_success += 1
            self.endpoint.error_callback(None)
            logging.warning("Exception from endpoint %s. Url: %s, exception: %s",
                            self.endpoint.name, self.endpoint.url, e)
            self.schedule_retry()
            return

        self._log_to_file(response)

        if response.status_code != 200:
            self.failures_without_success += 1
            self.endpoint.error_callback(response)
            logging.warning("Non-200 response %d from endpoint %s. Url: %s, response: %s",
                            response.status_code, self.endpoint.name, self.endpoint.url, response.content)
            self.schedule_retry()
            return

        parse_success = self.endpoint.parse_callback(response)
        if parse_success:
            self.failures_without_success = 0
            self.timer = threading.Timer(
                self.endpoint.refresh_interval.seconds, self.request_with_retries)
            self.timer.start()
        else:
            self.failures_without_success += 1
            self.schedule_retry()

    def schedule_retry(self) -> None:
        wait_time = self.endpoint.refresh_interval.seconds
        if self.failures_without_success == 1:
            wait_time = 1
        elif self.failures_without_success == 2:
            wait_time = 30

        self.timer = threading.Timer(wait_time, self.request_with_retries)
        self.timer.start()

    def _log_to_file(self, content: requests.models.Response) -> None:
        if _LOG_REQUESTS:
            filename = "debug/%d_%s.txt" % (int(time.time()),
                                            self.endpoint.name)
            with open(filename, 'w') as f:
                f.write(content.content.decode('utf-8'))


class HttpRequester(Requester):
    configured_endpoints: List[Endpoint]
    threads: List[RequesterThread]

    def __init__(self) -> None:
        self.configured_endpoints = []
        self.threads = []

    def add_endpoint(self, endpoint: Endpoint) -> None:
        self.configured_endpoints.append(endpoint)

    def start(self) -> None:
        self.threads = [RequesterThread(endpoint)
                        for endpoint in self.configured_endpoints]
        for t in self.threads:
            t.start()

    def stop(self) -> None:
        for t in self.threads:
            t.stop()
        self.threads = []
