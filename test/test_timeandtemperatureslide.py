import datetime
import unittest
from test.testing import TestDependencies, draw_and_compare

from dateutil import tz

from timeandtemperatureslide import TimeAndTemperatureSlide

_DEFAULT_CONFIG = {
    "observations_office": "TEST_O",
    "airnow_zip_code": "12345",
    "airnow_api_key": "API-KEY"
}
_DEFAULT_OBSERVATIONS_URL = "https://api.weather.gov/stations/TEST_O/observations/latest"
_DEFAULT_AIRNOW_URL = "https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=12345&API_KEY=API-KEY"


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
        self.deps.get_requester().expect(_DEFAULT_AIRNOW_URL,
                                         "timeandtemperatureslide_airnow_low_aqi.json")
        self.deps.get_requester().start()
        
        self.assertTrue(self.deps.get_requester().last_parse_successful)
        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_render", self.slide))

    def test_render_with_high_aqi(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().expect(_DEFAULT_AIRNOW_URL,
                                         "timeandtemperatureslide_airnow_high_aqi.json")
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_render_with_high_aqi", self.slide))

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

    def test_observations_reported_long_ago(self) -> None:
        # Date is more than 2 hours in the future beyond timestamp in file.
        test_datetime = datetime.datetime(
            2022, 5, 23, 14, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().start()

        self.assertFalse(self.deps.get_requester().last_parse_successful)
        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_observations_reported_long_ago", self.slide))

    def test_observations_become_stale(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().start()

        # Date becomes more than 2 hours in the future beyond timestamp in file.
        test_datetime = datetime.datetime(
            2022, 5, 23, 14, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.assertTrue(draw_and_compare(
            "TimeAndTemperatureSlide_observations_become_stale", self.slide))
