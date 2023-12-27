import datetime
from typing import Optional

import requests
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import RED, Align, draw_string
from glyphs import GlyphSet
from timesource import TimeSource
from requester import Endpoint


_REFRESH_INTERVAL = datetime.timedelta(minutes=5)
_STALENESS_THRESHOLD = datetime.timedelta(minutes=15)


class InternetStatusSlide(AbstractSlide):
    time_source: TimeSource
    last_successful_check: datetime.datetime

    def __init__(self, deps: Dependencies):
        self.time_source = deps.get_time_source()
        local_timezone = datetime.datetime.now().astimezone().tzinfo
        self.last_successful_check = datetime.datetime.min.replace(
            tzinfo=local_timezone)

        deps.get_requester().add_endpoint(Endpoint(
            name="internet_presence",
            url="http://gstatic.com/generate_204",
            refresh_interval=_REFRESH_INTERVAL,
            parse_callback=self._parse,
            error_callback=self._handle_error
        ))

    def _parse(self, response: requests.models.Response) -> bool:
        self.last_successful_check = self.time_source.now()
        return True

    def _handle_error(self, response: Optional[requests.models.Response]) -> None:
        pass

    def is_enabled(self) -> bool:
        return not self._internet_connected()

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        draw_string(draw, "NO", 32, 8, Align.CENTER, GlyphSet.FONT_7PX, RED)
        draw_string(draw, "INTERNET", 32, 16,
                    Align.CENTER, GlyphSet.FONT_7PX, RED)

    def _internet_connected(self) -> bool:
        return (self.time_source.now() - self.last_successful_check) < _STALENESS_THRESHOLD
