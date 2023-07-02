import datetime
import unittest
from test.testing import TestDependencies, draw_and_compare

from dateutil import tz

from forecastslide import ForecastSlide

_DEFAULT_CONFIG = {
    "forecast_office": "TEST_F",
}
_DEFAULT_FORECAST_URL = "https://api.weather.gov/gridpoints/TEST_F/forecast"


class ForecastSlideTest(unittest.TestCase):

    def setUp(self) -> None:
        self.deps = TestDependencies()
        self.slide = ForecastSlide(self.deps, _DEFAULT_CONFIG)

        self.test_datetime = datetime.datetime(
            2022, 6, 30, 15, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

    def test_render_evening(self) -> None:
        self.test_datetime = datetime.datetime(
            2022, 5, 23, 19, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_evening.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare("ForecastSlide_evening", self.slide))

    def test_render_afternoon(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "ForecastSlide_afternoon", self.slide))

    def test_render_missing_forecast(self) -> None:
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "ForecastSlide_missing_forecast", self.slide))

    def test_render_date_offset(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")

        config_with_offset = _DEFAULT_CONFIG.copy()
        config_with_offset["date_offset"] = 2
        slide_with_offset = ForecastSlide(self.deps, config_with_offset)
        self.deps.get_requester().start()
        self.assertTrue(draw_and_compare(
            "ForecastSlide_with_offset", slide_with_offset))

    def test_render_forecast_error_soon_after_success(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")
        self.deps.get_requester().start()

        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(minutes=60))
        self.deps.get_requester().clear_expectation(_DEFAULT_FORECAST_URL)
        self.deps.get_requester().start()

        # Slide should display the existing forecast, ignoring the error.
        # A dot should be displayed in the bottom right corner.
        self.assertTrue(draw_and_compare(
            "ForecastSlide_forecast_error_soon_after_success", self.slide))

    def test_render_forecast_error_long_after_success(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")
        self.deps.get_requester().start()

        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(hours=12))
        self.deps.get_requester().clear_expectation(_DEFAULT_FORECAST_URL)
        self.deps.get_requester().start()

        # Slide should not display a forecast because data is too old.
        self.assertTrue(draw_and_compare(
            "ForecastSlide_forecast_error_long_after_success", self.slide))

    def test_render_observations_error(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "ForecastSlide_missing_observations", self.slide))

    def test_render_all_error(self) -> None:
        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "ForecastSlide_missing_everything", self.slide))

    def test_render_null_current_temp(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(draw_and_compare(
            "ForecastSlide_null_current_temp", self.slide))
