import datetime
import unittest
from test.testing import TestDependencies, draw_and_compare

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

        self.test_datetime = datetime.datetime(
            2022, 6, 30, 15, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

    def test_render_evening(self) -> None:
        self.test_datetime = datetime.datetime(
            2022, 5, 23, 19, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_evening.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare("WeatherSlide_evening", self.slide))

    def test_render_afternoon(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare("WeatherSlide_afternoon", self.slide))

    def test_render_missing_forecast(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "WeatherSlide_missing_forecast", self.slide))

    def test_render_forecast_error_soon_after_success(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")
        self.deps.get_requester().start()

        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(minutes=60))
        self.deps.get_requester().clear_expectation(_DEFAULT_FORECAST_URL)
        self.deps.get_requester().start()

        # Slide should display the existing forecast, ignoring the error.
        # A dot should be displayed in the bottom right corner.
        self.assertTrue(draw_and_compare(
            "WeatherSlide_forecast_error_soon_after_success", self.slide))

    def test_render_forecast_error_long_after_success(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")
        self.deps.get_requester().start()

        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(hours=12))
        self.deps.get_requester().clear_expectation(_DEFAULT_FORECAST_URL)
        self.deps.get_requester().start()

        # Slide should not display a forecast because data is too old.
        self.assertTrue(draw_and_compare(
            "WeatherSlide_forecast_error_long_after_success", self.slide))

    def test_render_observations_error(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "WeatherSlide_missing_observations", self.slide))

    def test_render_all_error(self) -> None:
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "WeatherSlide_missing_everything", self.slide))

    def test_render_null_current_temp(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "weatherslide_observations_nulltemp.json")
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "weatherslide_forecast_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "WeatherSlide_null_current_temp", self.slide))
