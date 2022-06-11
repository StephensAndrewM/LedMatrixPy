import threading
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, List

import requests


@dataclass
class Endpoint:
    url: str
    refresh_interval: timedelta
    parser: Callable[[str], bool]
    error_callback: Callable[[requests.models.Response], None]


class Requester:
    def __init__(self) -> None:
        self.configured_endpoints: List[Endpoint] = []
        self.threads: List[RequesterThread] = []

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


class RequesterThread:
    endpoint: Endpoint
    timer: threading.Timer
    failures_without_success: int

    def __init__(self, endpoint: Endpoint) -> None:
        self.endpoint = endpoint
        self.failures_without_success = 0

    def start(self) -> None:
        self.request_with_retries()

    def stop(self) -> None:
        if self.timer is not None:
            self.timer.cancel()

    def request_with_retries(self) -> None:
        response = requests.get(self.endpoint.url)
        if response.status_code != 200:
            self.failures_without_success += 1
            self.endpoint.error_callback(response)
            self.schedule_retry()

        parse_success = self.endpoint.parser(response.text)
        if parse_success:
            self.failures_without_success = 0
            self.timer = threading.Timer(
                self.endpoint.refresh_interval.seconds, self.request_with_retries)
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
