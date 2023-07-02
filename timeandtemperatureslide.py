import datetime
import logging
from json import JSONDecodeError
from typing import Dict, Optional

import requests
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import (GRAY, RED, WHITE, YELLOW, Align, draw_glyph_by_name,
                     draw_string)
from requester import Endpoint
from timesource import TimeSource
from weatherutils import (NWS_HEADERS, celsius_to_fahrenheit,
                          icon_url_to_weather_glyph)

_OBSERVATIONS_REFRESH_INTERVAL = datetime.timedelta(minutes=5)
_OBSERVATIONS_STALENESS_THRESHOLD = datetime.timedelta(hours=2)


class TimeAndTemperatureSlide(AbstractSlide):
    time_source: TimeSource

    last_observations_retrieval: datetime.datetime
    current_temp: Optional[int]
    current_icon: Optional[str]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()

        local_timezone = datetime.datetime.now().astimezone().tzinfo
        self.last_observations_retrieval = datetime.datetime.min.replace(
            tzinfo=local_timezone)
        self.current_temp = None
        self.current_icon = None

        observations_office = options.get("observations_office", "KBOS")
        deps.get_requester().add_endpoint(Endpoint(
            name="weather_observations",
            url="https://api.weather.gov/stations/%s/observations/latest" % observations_office,
            refresh_interval=_OBSERVATIONS_REFRESH_INTERVAL,
            parse_callback=self._parse_observations,
            error_callback=self._handle_observations_error,
            headers=NWS_HEADERS,
        ))

    def _parse_observations(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode observations JSON: %s", response.content)
            return False

        if not "temperature" in data or data["temperature"]["value"] is None:
            logging.debug("Observations contain null temperature")
            return False

        # Assign all values at end in case an error returns otherwise.
        self.last_observations_retrieval = self.time_source.now()
        self.current_temp = int(
            celsius_to_fahrenheit(data["temperature"]["value"]))
        self.current_icon = icon_url_to_weather_glyph(data["icon"])

        return True

    def _handle_observations_error(self, response: Optional[requests.models.Response]) -> None:
        # No error handling is needed since we'll display the old value until it expires.
        pass

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        now = self.time_source.now()

        observations_time_delta = self.time_source.now() - self.last_observations_retrieval
        time_y_offset = 0
        if (self.current_temp is not None
                and observations_time_delta <= _OBSERVATIONS_STALENESS_THRESHOLD):
            if self.current_icon:
                draw_glyph_by_name(draw, self.current_icon, 0, 17, WHITE)
            else:
                draw_string(draw, "?", 6, 21, Align.LEFT, GRAY)
            draw_string(draw, "%d°" % self.current_temp,
                        18, 21, Align.LEFT, WHITE)

            # Show a subtle indicator that this data is mildly stale.
            if (observations_time_delta > _OBSERVATIONS_REFRESH_INTERVAL*2):
                draw.point((0, 31), GRAY)
        else:
            # Push down the date and time if there we don't have current conditions.
            time_y_offset = 8

        date_string = now.strftime("%a %b %-d").upper()
        draw_string(draw, date_string, 0, time_y_offset+0, Align.LEFT, YELLOW)
        time_string = now.strftime("%-I:%M %p")
        draw_string(draw, time_string, 0, time_y_offset+8, Align.LEFT, YELLOW)
