import datetime
from test.testing import SlideTest

from dateutil import tz

from christmasslide import ChristmasSlide


class ChristmasSlideTest(SlideTest):

    def test_24days(self) -> None:
        test_datetime = datetime.datetime(
            2022, 12, 1, 19, 31, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        slide = ChristmasSlide(self.deps)

        self.assertTrue(slide.is_enabled())
        self.assertRenderMatchesGolden(slide)

    def test_3days(self) -> None:
        test_datetime = datetime.datetime(
            2022, 12, 22, 19, 31, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        slide = ChristmasSlide(self.deps)

        self.assertTrue(slide.is_enabled())
        self.assertRenderMatchesGolden(slide)

    def test_not_nabled_after_christmas(self) -> None:
        test_datetime = datetime.datetime(
            2022, 12, 26, 19, 31, tzinfo=tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        slide = ChristmasSlide(self.deps)
        self.assertFalse(slide.is_enabled())
