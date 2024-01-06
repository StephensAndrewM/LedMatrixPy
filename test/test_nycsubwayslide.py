import datetime
from test.testing import SlideTest

from dateutil import tz

from gtfs_realtime_pb2 import FeedMessage  # type: ignore
from nycsubwayslide import NycSubwaySlide

_DEFAULT_CONFIG = {
    "mta_api_key": "API-KEY",
}
_NQRW_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
_BDFM_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
_ACE_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"


class NycSubwaySlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        test_datetime = datetime.datetime(
            2023, 10, 30, 17, 55, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)
        self.slide = NycSubwaySlide(self.deps, _DEFAULT_CONFIG)

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
        self.deps.get_requester().expect_with_proto_response(
            _ACE_URL, "mta_ace.textproto", FeedMessage())
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)


    def test_has_departures_all_lines(self) -> None:
        self.deps.get_requester().expect_with_proto_response(
            _NQRW_URL, "mta_nqrw.textproto", FeedMessage())
        self.deps.get_requester().expect_with_proto_response(
            _BDFM_URL, "mta_bdfm.textproto", FeedMessage())
        self.deps.get_requester().expect_with_proto_response(
            _ACE_URL, "mta_ace.textproto", FeedMessage())
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertRenderMatchesGolden(self.slide)

