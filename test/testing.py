from datetime import datetime

from constants import GRID_HEIGHT, GRID_WIDTH
from deps import Dependencies
from drawing import PixelGrid
from PIL import Image, ImageChops  # type: ignore
from timesource import TimeSource


class FakeTimeSource(TimeSource):
    clock_time: datetime

    def set(self, now: datetime) -> None:
        self.clock_time = now

    def now(self) -> datetime:
        return self.clock_time


class TestDependencies(Dependencies):
    time_source: FakeTimeSource

    def __init__(self) -> None:
        self.time_source = FakeTimeSource()

    def get_time_source(self) -> TimeSource:
        return self.time_source


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
