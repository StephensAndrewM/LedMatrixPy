import datetime
from test.testing import SlideTest

from dateutil import tz

from internetstatusslide import InternetStatusSlide

_PRESENCE_URL = "http://gstatic.com/generate_204"


class InternetStatusSlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        self.test_datetime = datetime.datetime(
            2023, 10, 30, 17, 55, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(self.test_datetime)
        self.slide = InternetStatusSlide(self.deps)

    def test_internet_not_present(self) -> None:
        self.deps.get_requester().expect(_PRESENCE_URL, "gstatic_ok.json")
        self.deps.get_requester().start()
        self.deps.time_source.set(
            self.test_datetime + datetime.timedelta(minutes=20))
        self.deps.get_requester().clear_expectation(_PRESENCE_URL)
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_internet_present(self) -> None:
        self.deps.get_requester().expect(_PRESENCE_URL, "gstatic_ok.json")
        self.deps.get_requester().start()

        # Message is still displayed but the slide would be disabled so it's okay.
        self.assertFalse(self.slide.is_enabled())
