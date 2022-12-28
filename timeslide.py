from PIL import ImageDraw  # type: ignore

from abstractslide import AbstractSlide
from deps import Dependencies
from drawing import WHITE, YELLOW, Align, draw_string
from timesource import TimeSource


class TimeSlide(AbstractSlide):
    time_source: TimeSource

    def __init__(self, deps: Dependencies):
        self.time_source = deps.get_time_source()

    def draw(self, img: ImageDraw) -> None:
        now = self.time_source.now()

        weekday_string = now.strftime("%A").upper()
        draw_string(img, weekday_string,
                    2, 7, Align.LEFT, WHITE)
        date_string = "%s %d" % (now.strftime("%B").upper(),
                                 now.day)
        draw_string(img, date_string, 2, 17, Align.LEFT, WHITE)

        time_string = now.strftime("%l:%M %p")
        draw_string(img, time_string, 125, 12, Align.RIGHT, YELLOW)
