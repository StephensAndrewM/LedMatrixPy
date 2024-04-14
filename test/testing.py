import inspect
import unittest
from datetime import datetime
from typing import Dict, List

import requests
from google.protobuf import message, text_format
from PIL import Image, ImageChops  # type: ignore

from abstractslide import AbstractSlide
from deps import Dependencies
from drawing import create_slide
from requester import Endpoint, Requester
from timesource import TimeSource


class FakeTimeSource(TimeSource):
    clock_time: datetime

    def set(self, now: datetime) -> None:
        if now.tzinfo is None:
            print(
                "Warning! Set the time zone on the testing datetime to match the real version.")
        self.clock_time = now

    def now(self) -> datetime:
        return self.clock_time


_DEFAULT_ERROR_RESPONSE = requests.models.Response()
_DEFAULT_ERROR_RESPONSE.status_code = 404


class FakeRequester(Requester):
    configured_endpoints: List[Endpoint]
    expected_responses: Dict[str, requests.models.Response]
    last_parse_successful: bool

    def __init__(self) -> None:
        self.configured_endpoints = []
        self.expected_responses = {}
        self.last_parse_successful = False

    def add_endpoint(self, endpoint: Endpoint) -> None:
        self.configured_endpoints.append(endpoint)

    def start(self) -> None:
        for endpoint in self.configured_endpoints:
            url = endpoint.get_url()
            if url is None:
                continue
            if url in self.expected_responses:
                self.last_parse_successful = endpoint.parse_callback(
                    self.expected_responses[url])
            else:
                endpoint.error_callback(_DEFAULT_ERROR_RESPONSE)

    def stop(self) -> None:
        pass

    def expect_with_proto_response(self, url: str, file: str, message: message) -> None:
        with open("test/data/responses/" + file) as f:
            content = text_format.Parse(f.read(), message).SerializeToString()
            self.set_expectation(url, content)

    def expect(self, url: str, file: str) -> None:
        with open("test/data/responses/" + file) as f:
            content = str.encode(f.read())  # type: ignore
            self.set_expectation(url, content)

    def set_expectation(self, url: str, content: bytes) -> None:
        response = requests.models.Response()
        response.status_code = 200
        response._content = content
        self.expected_responses[url] = response

    def clear_expectation(self, url: str) -> None:
        self.expected_responses.pop(url, None)


class TestDependencies(Dependencies):
    time_source: FakeTimeSource

    def __init__(self) -> None:
        self.time_source = FakeTimeSource()
        self.requester = FakeRequester()

    def get_time_source(self) -> FakeTimeSource:
        return self.time_source

    def get_requester(self) -> FakeRequester:
        return self.requester


_GOLDEN_DIR = "test/data/golden"


class SlideTest(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.deps = TestDependencies()

    def assertRendersBlank(self, slide: AbstractSlide) -> None:
        actual_img = create_slide(slide.get_type())
        slide.draw(actual_img)
        blank_img = create_slide(slide.get_type())
        diff = ImageChops.difference(actual_img, blank_img)
        if diff.getbbox():
            image_name_base = self._image_name_from_test_name()
            actual_img_filename = "%s/%s_actual.png" % (
                _GOLDEN_DIR, image_name_base)
            actual_img.save(actual_img_filename)
            raise AssertionError(
                "Expected no output, but something was rendered. Saved candidate to %s" % actual_img_filename)

    def assertRenderMatchesGolden(self, slide: AbstractSlide) -> None:
        if not slide.is_enabled():
            raise AssertionError("Cannot compare to golden because slide is not enabled")

        actual_img = create_slide(slide.get_type())
        slide.draw(actual_img)
        image_name_base = self._image_name_from_test_name()
        self._compare_to_golden(image_name_base, actual_img)

    def assertImageMatchesGolden(self, actual_img: Image) -> None:
        image_name_base = self._image_name_from_test_name()
        self._compare_to_golden(image_name_base, actual_img)

    def _image_name_from_test_name(self) -> str:
        calling_function = inspect.stack()[2].function.replace("test_", "")
        subclass = type(self).__name__.replace("Test", "")
        return subclass + "_" + calling_function

    def _compare_to_golden(self, image_name_base: str, actual_img: Image) -> bool:
        expected_img_filename = "%s/%s_golden.png" % (
            _GOLDEN_DIR, image_name_base)
        actual_img_filename = "%s/%s_actual.png" % (
            _GOLDEN_DIR, image_name_base)
        try:
            with Image.open(expected_img_filename) as expected_img:
                diff = ImageChops.difference(actual_img, expected_img)

                if actual_img.width != expected_img.width or actual_img.height != expected_img.height:
                    raise AssertionError("Output and golden images had different dimensions. Output: %dx%d, Golden: %dx%d" % (
                        actual_img.width, actual_img.height, expected_img.width, expected_img.height))

                elif diff.getbbox():
                    diff_img_filename = "%s/%s_diff.png" % (
                        _GOLDEN_DIR, image_name_base)
                    diff.save(diff_img_filename)
                    actual_img.save(actual_img_filename)
                    raise AssertionError("Output differed from %s. Saved candidate image to %s, diff to %s" % (
                        expected_img_filename, actual_img_filename, diff_img_filename))

        except FileNotFoundError:
            actual_img.save(actual_img_filename)
            raise AssertionError("Golden image %s does not exist. Saved %s as a candidate." % (
                expected_img_filename, actual_img_filename))


def draw_and_compare(golden_image_name: str, slide: AbstractSlide) -> bool:
    img = create_slide(slide.get_type())
    slide.draw(img)
    return compare_to_golden(golden_image_name, img)


def compare_to_golden(golden_image_name: str, actual_img: Image) -> bool:
    expected_img_filename = "test/data/golden/%s_golden.png" % golden_image_name
    try:
        with Image.open(expected_img_filename) as expected_img:
            diff = ImageChops.difference(actual_img, expected_img)

            if actual_img.width != expected_img.width or actual_img.height != expected_img.height:
                print("Output and golden images had different dimensions. Output: %dx%d, Golden: %dx%d" % (
                    actual_img.width, actual_img.height, expected_img.width, expected_img.height))
            elif diff.getbbox():
                print("Output differed from %s" % expected_img_filename)
                diff.save("test/data/golden/%s_diff.png" % golden_image_name)
            else:
                return True

    except FileNotFoundError:
        print("Golden image %s does not exist" % expected_img_filename)

    actual_img.save("test/data/golden/%s_actual.png" % golden_image_name)
    return False
