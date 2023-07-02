import datetime
import unittest
from test.testing import TestDependencies, draw_and_compare

from dateutil import tz

from timeandtemperatureslide import TimeAndTemperatureSlide

_DEFAULT_CONFIG = {
    "observations_office": "TEST_O",
}
_DEFAULT_OBSERVATIONS_URL = "https://api.weather.gov/stations/TEST_O/observations/latest"


class TimeAndTemperatureSlideTest(unittest.TestCase):

    def setUp(self) -> None:
        self.deps = TestDependencies()
        self.slide = TimeAndTemperatureSlide(self.deps, _DEFAULT_CONFIG)

        # This creates the widest possible time string.
        self.test_datetime = datetime.datetime(
            2022, 5, 23, 12, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

    def test_render(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_render", self.slide))

    def test_missing_observations(self) -> None:
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_missing_observations", self.slide))

    def test_null_current_temp(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_nulltemp.json")
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_null_current_temp", self.slide))

    def test_unknown_icon(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_unknown_icon.json")
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_unknown_icon", self.slide))
