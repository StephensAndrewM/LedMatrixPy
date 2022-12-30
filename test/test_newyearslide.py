import unittest
from datetime import datetime
from test.testing import TestDependencies, draw_and_compare

from dateutil import tz

from newyearslide import NewYearSlide


class NewYearSlideTest(unittest.TestCase):

    def test_render_near_midnight(self) -> None:
        deps = TestDependencies()
        test_datetime = datetime(
            2020, 12, 31, 20, 31, 59, 0, tz.gettz("America/New_York"))
        deps.time_source.set(test_datetime)

        slide = NewYearSlide(deps)
        self.assertTrue(draw_and_compare("NewYearSlide_before_midnight", slide))

    def test_render_after_midnight(self) -> None:
        deps = TestDependencies()
        test_datetime = datetime(
            2021, 1, 1, 0, 31, 0, 0, tz.gettz("America/New_York"))
        deps.time_source.set(test_datetime)

        slide = NewYearSlide(deps)
        self.assertTrue(draw_and_compare("NewYearSlide_after_midnight", slide))
