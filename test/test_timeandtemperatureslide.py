import datetime
from test.testing import SlideTest

from dateutil import tz

from timeandtemperatureslide import TimeAndTemperatureSlide

_DEFAULT_CONFIG = {
    "observations_office": "TEST_O",
    "airnow_zip_code": "12345",
    "airnow_api_key": "API-KEY"
}
_DEFAULT_OBSERVATIONS_URL = "https://api.weather.gov/stations/TEST_O/observations/latest"
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
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().expect(_DEFAULT_AIRNOW_URL,
                                         "timeandtemperatureslide_airnow_low_aqi.json")
        self.deps.get_requester().start()

        self.assertTrue(self.deps.get_requester().last_parse_successful)
        self.assertRenderMatchesGolden(self.slide)

    def test_render_with_high_aqi(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().expect(_DEFAULT_AIRNOW_URL,
                                         "timeandtemperatureslide_airnow_high_aqi.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_missing_observations(self) -> None:
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_null_current_temp(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_nulltemp.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_unknown_icon(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_unknown_icon.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_observations_reported_long_ago(self) -> None:
        # Date is more than 3 hours in the future beyond timestamp in file.
        test_datetime = datetime.datetime(
            2022, 5, 23, 14, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().start()

        self.assertFalse(self.deps.get_requester().last_parse_successful)
        self.assertRenderMatchesGolden(self.slide)

    def test_observations_become_stale(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_OBSERVATIONS_URL,
                                         "timeandtemperatureslide_standard.json")
        self.deps.get_requester().start()

        # Date becomes more than 3 hours in the future beyond timestamp in file.
        test_datetime = datetime.datetime(
            2022, 5, 23, 14, 34, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.assertRenderMatchesGolden(self.slide)
