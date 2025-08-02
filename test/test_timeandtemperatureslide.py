import datetime
from test.testing import SlideTest

from dateutil import tz

from timeandtemperatureslide import TimeAndTemperatureSlide

_DEFAULT_CONFIG = {
    "weather_lat": "1.2345",
    "weather_lng": "-5.6789",
    "openweather_api_key": "OW-API-KEY",
    "airnow_zip_code": "12345",
    "airnow_api_key": "API-KEY"
}
_DEFAULT_OBSERVATIONS_URL = "https://api.openweathermap.org/data/3.0/onecall?lat=1.2345&lon=-5.6789&exclude=minutely,hourly,daily,alerts&units=imperial&appid=OW-API-KEY"
_DEFAULT_AIRNOW_URL = "https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=12345&API_KEY=API-KEY"


class TimeAndTemperatureSlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        # This creates the widest possible time string.
        self.test_datetime = datetime.datetime(
            2022, 5, 23, 12, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)

        self.slide = TimeAndTemperatureSlide(self.deps, _DEFAULT_CONFIG)

    def test_render(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_current.json")
        self.deps.get_requester().expect(_DEFAULT_AIRNOW_URL,
                                         "timeandtemperatureslide_airnow_low_aqi.json")
        self.deps.get_requester().start()

        self.assertTrue(self.deps.get_requester().last_parse_successful)
        self.assertRenderMatchesGolden(self.slide)

    def test_render_with_high_aqi(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_current.json")
        self.deps.get_requester().expect(_DEFAULT_AIRNOW_URL,
                                         "timeandtemperatureslide_airnow_high_aqi.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_missing_observations(self) -> None:
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_observations_become_stale(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_current.json")
        self.deps.get_requester().start()

        # Date becomes more than 3 hours in the future beyond the last successful response.
        test_datetime = datetime.datetime(
            2022, 5, 23, 16, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.assertRenderMatchesGolden(self.slide)
