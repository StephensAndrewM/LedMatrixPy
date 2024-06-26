import datetime
from test.testing import SlideTest

from dateutil import tz

from forecastslide import ForecastSlide

_DEFAULT_CONFIG = {
    "forecast_office": "TEST_F",
}
_DEFAULT_FORECAST_URL = "https://api.weather.gov/gridpoints/TEST_F/forecast"


class ForecastSlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        self.slide = ForecastSlide(self.deps, _DEFAULT_CONFIG)

        self.test_datetime = datetime.datetime(
            2022, 6, 30, 15, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

    def test_evening(self) -> None:
        self.test_datetime = datetime.datetime(
            2022, 5, 23, 19, 31, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_evening.json")

        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)

    def test_afternoon(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")

        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)

    def test_missing_forecast(self) -> None:
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())
        self.assertRendersBlank(self.slide)

    def test_with_offset(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")

        config_with_offset = _DEFAULT_CONFIG.copy()
        config_with_offset["date_offset"] = "2"
        slide_with_offset = ForecastSlide(self.deps, config_with_offset)
        self.deps.get_requester().start()
        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(slide_with_offset)

    def test_forecast_error_soon_after_success(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")
        self.deps.get_requester().start()

        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(minutes=60))
        self.deps.get_requester().clear_expectation(_DEFAULT_FORECAST_URL)
        self.deps.get_requester().start()

        # Slide should display the existing forecast, ignoring the error.
        # A dot should be displayed in the bottom right corner.
        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)

    def test_forecast_error_long_after_success(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_FORECAST_URL,
                                         "forecastslide_afternoon.json")
        self.deps.get_requester().start()

        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(hours=12))
        self.deps.get_requester().clear_expectation(_DEFAULT_FORECAST_URL)
        self.deps.get_requester().start()

        # Slide should not display a forecast because data is too old.
        self.assertFalse(self.slide.is_enabled())
        self.assertRendersBlank(self.slide)
