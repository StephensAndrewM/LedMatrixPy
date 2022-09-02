import unittest
from datetime import datetime
from test.testing import TestDependencies, compare_to_golden

from timeslide import TimeSlide


class TimeSlideTest(unittest.TestCase):

    def test_render_time(self) -> None:
        deps = TestDependencies()
        # September is the longest month name, with a 2-digit number.
        test_datetime = datetime(2020, 9, 22, 19, 31, 0, 0)
        deps.time_source.set(test_datetime)

        slide = TimeSlide(deps)
        grid = slide.draw()

        self.assertTrue(compare_to_golden("TimeSlide", grid))
