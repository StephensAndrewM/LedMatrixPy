import datetime
import unittest
from test.testing import TestDependencies, draw_and_compare

from dateutil import tz

from gtfs_realtime_pb2 import FeedMessage  # type: ignore
from nycsubwayslide import NycSubwaySlide

_DEFAULT_CONFIG = {
    "mta_api_key": "API-KEY",
}
_NQRW_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
_BDFM_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
_ACE_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"


class NycSubwaySlideTest(unittest.TestCase):

    def setUp(self) -> None:
        self.deps = TestDependencies()
        test_datetime = datetime.datetime(
            2023, 10, 30, 17, 55, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)
        self.slide = NycSubwaySlide(self.deps, _DEFAULT_CONFIG)

    def test_render_has_no_departures(self) -> None:
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())
        # Slide should be blank.
        self.assertTrue(draw_and_compare(
            "NycSubwaySlide_has_no_departures", self.slide))

    def test_render_has_departures_one_line(self) -> None:
        self.deps.get_requester().expect_with_proto_response(
            _NQRW_URL, "mta_nqrw.textproto", FeedMessage())
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertTrue(draw_and_compare(
            "NycSubwaySlide_has_departures_one_line", self.slide))

    def test_render_has_departures_two_lines(self) -> None:
        self.deps.get_requester().expect_with_proto_response(
            _NQRW_URL, "mta_nqrw.textproto", FeedMessage())
        self.deps.get_requester().expect_with_proto_response(
            _ACE_URL, "mta_ace.textproto", FeedMessage())
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertTrue(draw_and_compare(
            "NycSubwaySlide_has_departures_two_lines", self.slide))

    def test_render_has_departures_all_lines(self) -> None:
        self.deps.get_requester().expect_with_proto_response(
            _NQRW_URL, "mta_nqrw.textproto", FeedMessage())
        self.deps.get_requester().expect_with_proto_response(
            _BDFM_URL, "mta_bdfm.textproto", FeedMessage())
        self.deps.get_requester().expect_with_proto_response(
            _ACE_URL, "mta_ace.textproto", FeedMessage())
        self.deps.get_requester().start()

        self.assertTrue(self.slide.is_enabled())
        self.assertTrue(draw_and_compare(
            "NycSubwaySlide_has_departures_all_lines", self.slide))
