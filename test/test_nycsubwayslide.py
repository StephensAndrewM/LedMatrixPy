import datetime
from test.testing import SlideTest

from dateutil import tz

from gtfs_realtime_pb2 import FeedMessage  # type: ignore
from nycsubwayslide import NycSubwaySlide

_DEFAULT_CONFIG = {
    "mta_api_key": "API-KEY",
    "mta_bus_api_key": "BUS-API-KEY",
    "mta_q_stop_id": "D26N",
    "mta_b41_stop_id": "STOP_REF",
}
_NQRW_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
_B41_URL = "https://bustime-classic.mta.info/api/siri/stop-monitoring.json?key=BUS-API-KEY&version=2&OperatorRef=MTA&MonitoringRef=STOP_REF"

class NycSubwaySlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        test_datetime = datetime.datetime(
            2023, 10, 30, 17, 55, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)
        self.slide = NycSubwaySlide(self.deps, _DEFAULT_CONFIG)

    def test_error_response(self) -> None:
        self.deps.get_requester().expect(_NQRW_URL, "forecastslide_afternoon.json")
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())

    def test_has_no_departures(self) -> None:
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())
        self.assertRendersBlank(self.slide)

    def test_has_departures_one_line(self) -> None:
        self.deps.get_requester().expect_with_proto_response(
            _NQRW_URL, "mta_nqrw.textproto", FeedMessage())
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)

    def test_has_departures_two_lines(self) -> None:
        self.deps.get_requester().expect_with_proto_response(
                    _NQRW_URL, "mta_nqrw.textproto", FeedMessage())
        self.deps.get_requester().expect(_B41_URL, "mta_b41.json")
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)
