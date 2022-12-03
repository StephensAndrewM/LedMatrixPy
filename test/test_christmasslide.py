import datetime
import unittest
from test.testing import TestDependencies, compare_to_golden

from dateutil import tz

from christmasslide import ChristmasSlide


class ChristmasSlideTest(unittest.TestCase):

    def test_render_24_before_christmas(self) -> None:
        deps = TestDependencies()
        test_datetime = datetime.datetime(
            2022, 12, 1, 19, 31, tzinfo=tz.gettz("America/New_York"))
        deps.time_source.set(test_datetime)

        slide = ChristmasSlide(deps)
        grid = slide.draw()

        self.assertTrue(slide.is_enabled())
        self.assertTrue(compare_to_golden("ChristmasSlide_24days", grid))

    def test_render_3_before_christmas(self) -> None:
        deps = TestDependencies()
        test_datetime = datetime.datetime(
            2022, 12, 22, 19, 31, tzinfo=tz.gettz("America/New_York"))
        deps.time_source.set(test_datetime)

        slide = ChristmasSlide(deps)
        grid = slide.draw()

        self.assertTrue(slide.is_enabled())
        self.assertTrue(compare_to_golden("ChristmasSlide_3days", grid))

    def test_isenabled_after_christmas(self) -> None:
        deps = TestDependencies()
        test_datetime = datetime.datetime(
            2022, 12, 26, 19, 31, tzinfo=tz.gettz("America/New_York"))
        deps.time_source.set(test_datetime)

        slide = ChristmasSlide(deps)
        self.assertFalse(slide.is_enabled())
