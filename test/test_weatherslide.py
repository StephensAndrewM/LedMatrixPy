import datetime
import unittest
from test.testing import TestDependencies, compare_to_golden

from dateutil import tz
from weatherslide import WeatherSlide

_DEFAULT_CONFIG = {
    "observations_office": "TEST_O",
    "forecast_office": "TEST_F",
}
_DEFAULT_OBSERVATIONS_URL = "https://api.weather.gov/stations/TEST_O/observations/latest"
_DEFAULT_FORECAST_URL = "https://api.weather.gov/gridpoints/TEST_F/forecast"


class WeatherSlideTest(unittest.TestCase):

    def setUp(self) -> None:
        self.deps = TestDependencies()
        self.slide = WeatherSlide(self.deps, _DEFAULT_CONFIG)

    def test_render_evening(self) -> None:
        test_datetime = datetime.datetime(
            2022, 5, 23, 19, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_evening.json")

        self.deps.get_requester().start()
        grid = self.slide.draw()

        self.assertTrue(compare_to_golden("WeatherSlide_evening", grid))

    def test_render_afternoon(self) -> None:
        test_datetime = datetime.datetime(
            2022, 6, 30, 15, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")

        self.deps.get_requester().start()
        grid = self.slide.draw()

        self.assertTrue(compare_to_golden("WeatherSlide_afternoon", grid))

    def test_render_forecast_error(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")

        self.deps.get_requester().start()
        grid = self.slide.draw()

        self.assertTrue(compare_to_golden(
            "WeatherSlide_missing_forecast", grid))

    def test_render_observations_error(self) -> None:
        test_datetime = datetime.datetime(
            2022, 6, 30, 15, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")

        self.deps.get_requester().start()
        grid = self.slide.draw()

        self.assertTrue(compare_to_golden(
            "WeatherSlide_missing_observations", grid))

    def test_render_all_error(self) -> None:
        self.deps.get_requester().start()
        grid = self.slide.draw()

        self.assertTrue(compare_to_golden(
            "WeatherSlide_missing_everything", grid))

    def test_render_null_current_temp(self) -> None:
        test_datetime = datetime.datetime(
            2022, 6, 30, 15, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations_nulltemp.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")

        self.deps.get_requester().start()
        grid = self.slide.draw()

        self.assertTrue(compare_to_golden(
            "WeatherSlide_null_current_temp", grid))
