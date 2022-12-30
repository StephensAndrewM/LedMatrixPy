import datetime

from PIL import ImageDraw  # type: ignore

from abstractslide import AbstractSlide
from deps import Dependencies
from drawing import WHITE, YELLOW, Align, draw_string
from timesource import TimeSource


class NewYearSlide(AbstractSlide):
    time_source: TimeSource
    target_year: int
    target_datetime: datetime.datetime

    def __init__(self, deps: Dependencies):
        self.time_source = deps.get_time_source()
        now = self.time_source.now()
        self.target_year = now.year + 1
        # If the date has rolled over to January, don't change target year yet.
        if now.month == 1:
            self.target_year = now.year
        
        self.target_datetime = datetime.datetime(
            self.target_year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)

    def draw(self, img: ImageDraw) -> None:
        now = self.time_source.now()
        diff = self.target_datetime - now
        diff_seconds = diff.total_seconds()

        diff_string = '{:02} : {:02} : {:02}'.format(
            int(diff_seconds // 3600), int(diff_seconds % 3600 // 60), int(diff_seconds % 60))

        # Don't count in reverse
        if diff_seconds < 0:
            diff_string = "00 : 00 : 00"

        draw_string(img, diff_string, 64, 6, Align.CENTER, WHITE)

        draw_string(img, "UNTIL %d" % self.target_year,
                    64, 18, Align.CENTER, YELLOW)
