from datetime import datetime
from typing import Dict, List

import requests
from constants import GRID_HEIGHT, GRID_WIDTH
from deps import Dependencies
from drawing import PixelGrid
from PIL import Image, ImageChops  # type: ignore
from requester import Endpoint, Requester
from timesource import TimeSource


class FakeTimeSource(TimeSource):
    clock_time: datetime

    def set(self, now: datetime) -> None:
        self.clock_time = now

    def now(self) -> datetime:
        return self.clock_time


_DEFAULT_ERROR_RESPONSE = requests.models.Response()
_DEFAULT_ERROR_RESPONSE.status_code = 404


class FakeRequester(Requester):
    configured_endpoints: List[Endpoint]
    expected_responses: Dict[str, requests.models.Response]

    def __init__(self) -> None:
        self.configured_endpoints = []
        self.expected_responses = {}

    def add_endpoint(self, endpoint: Endpoint) -> None:
        self.configured_endpoints.append(endpoint)

    def start(self) -> None:
        for endpoint in self.configured_endpoints:
            if endpoint.url in self.expected_responses:
                endpoint.parse_callback(self.expected_responses[endpoint.url])
            else:
                endpoint.error_callback(_DEFAULT_ERROR_RESPONSE)

    def stop(self) -> None:
        pass

    def expect(self, url: str, file: str) -> None:
        with open("test/data/responses/" + file) as f:
            response = requests.models.Response()
            response.status_code = 200
            response._content = str.encode(f.read())
            self.expected_responses[url] = response


class TestDependencies(Dependencies):
    time_source: FakeTimeSource

    def __init__(self) -> None:
        self.time_source = FakeTimeSource()
        self.requester = FakeRequester()

    def get_time_source(self) -> FakeTimeSource:
        return self.time_source

    def get_requester(self) -> FakeRequester:
        return self.requester


def compare_to_golden(golden_image_name: str, actual_grid: PixelGrid) -> bool:
    actual_img = actual_grid.as_image()
    expected_img_filename = "test/data/golden/%s_golden.png" % golden_image_name
    try:
        with Image.open(expected_img_filename) as expected_img:
            diff = ImageChops.difference(actual_img, expected_img)

            if list(actual_img.getdata()) == list(expected_img.getdata()):
                return True
            else:
                print("Output differed from %s" % expected_img_filename)

    except FileNotFoundError:
        print("Golden image %s does not exist" % expected_img_filename)

    actual_img.save("test/data/golden/%s_actual.png" % golden_image_name)
    return False
