import datetime
import logging
from typing import Dict, List, Optional

import requests
from dateutil import tz
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import (BLACK, GRAY, ORANGE, WHITE, YELLOW, Align, Color,
                     draw_string)
from glyphs import GlyphSet
from gtfs_realtime_pb2 import FeedMessage  # type: ignore
from requester import Endpoint
from timesource import TimeSource

_REFRESH_INTERVAL = datetime.timedelta(minutes=1)
_STALENESS_THRESHOLD = datetime.timedelta(minutes=10)
_DEPARTURE_LOWER_BOUND = datetime.timedelta(minutes=5)
_MAX_NUM_PREDICTIONS = 2


class NycSubwaySlide(AbstractSlide):
    time_source: TimeSource
    departures: Dict[str, List[datetime.datetime]]
    last_updated: Dict[str, datetime.datetime]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()
        self.departures = {}
        self.last_updated = {}
        headers = {"x-api-key": options.get("mta_api_key", "")}

        deps.get_requester().add_endpoint(Endpoint(
            name="mta_nqrw",
            url="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
            refresh_interval=_REFRESH_INTERVAL,
            parse_callback=self._parse_q,
            error_callback=self._handle_error,
            headers=headers,
        ))
        deps.get_requester().add_endpoint(Endpoint(
            name="mta_bdfm",
            url="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
            refresh_interval=_REFRESH_INTERVAL,
            parse_callback=self._parse_b,
            error_callback=self._handle_error,
            headers=headers,
        ))
        # Interestingly, the Franklin Avenue Shuttle is provided here
        deps.get_requester().add_endpoint(Endpoint(
            name="mta_ace",
            url="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
            refresh_interval=_REFRESH_INTERVAL,
            parse_callback=self._parse_s,
            error_callback=self._handle_error,
            headers=headers,
        ))

    def _parse_q(self, response: requests.models.Response) -> bool:
        return self._parse(response, "Q")

    def _parse_b(self, response: requests.models.Response) -> bool:
        return self._parse(response, "B")

    def _parse_s(self, response: requests.models.Response) -> bool:
        return self._parse(response, "FS")

    def _parse(self, response: requests.models.Response, expected_line: str) -> bool:
        try:
            data = FeedMessage()
            data.ParseFromString(response.content)
        except IOError:
            logging.warning(
                "Failed to decode GTFS realtime proto: %s", response.content)
            return False

        departures = []
        for entity in data.entity:
            line = entity.trip_update.trip.route_id
            if line == expected_line:
                for update in entity.trip_update.stop_time_update:
                    # Check for Prospect Park North only
                    if update.stop_id == "D26N":
                        t = datetime.datetime.fromtimestamp(
                            update.departure.time, tz.gettz("America/New_York"))
                        departures.append(t)
        # Departures aren't always given in order, so sort them before storing.
        self.departures[expected_line] = sorted(departures)
        self.last_updated[expected_line] = self.time_source.now()
        return True

    def _handle_error(self, response: Optional[requests.models.Response]) -> None:
        # No error handling is needed since we'll display the old value until it expires.
        pass

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def is_enabled(self) -> bool:
        # Slide should not be shown if there is no data at all.
        return self._get_num_lines() > 0

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        now = self.time_source.now()

        num_lines = self._get_num_lines()
        if num_lines == 1:
            start_y = 11
            line_height = 0
        elif num_lines == 2:
            start_y = 3
            line_height = 14
        else:
            start_y = 0
            line_height = 11

        next_line_y = start_y
        if self._has_predictions("Q"):
            self._draw_prediction_line(
                draw, now, next_line_y, "Q", "Q", YELLOW)
            next_line_y += line_height

        if self._has_predictions("B"):
            self._draw_prediction_line(
                draw, now, next_line_y, "B", "B", ORANGE)
            next_line_y += line_height

        if self._has_predictions("FS"):
            self._draw_prediction_line(draw, now, next_line_y, "FS", "S", GRAY)

    def _get_num_lines(self) -> int:
        return sum([self._has_predictions(line) for line in ["Q", "B", "FS"]])

    def _draw_prediction_line(self, draw: ImageDraw, now: datetime.datetime, y: int, line_key: str, line_label: str, color: Color) -> None:
        draw.ellipse([(0, y), (10, y+10)], fill=color)
        draw_string(draw, line_label + " ", 3, y+2,
                    Align.LEFT, GlyphSet.FONT_7PX, BLACK)
        departure_strings: List[str] = []
        for departure in self.departures[line_key]:
            diff = (departure - now)
            if diff >= _DEPARTURE_LOWER_BOUND and len(departure_strings) < _MAX_NUM_PREDICTIONS:
                departure_strings.append("%d" % (diff.total_seconds() // 60))
        draw_string(draw, (", ".join(departure_strings)) +
                    " min", 14, y+2, Align.LEFT, GlyphSet.FONT_7PX, WHITE)

    def _has_predictions(self, line_key: str) -> bool:
        now = self.time_source.now()
        if line_key in self.last_updated:
            if now - self.last_updated[line_key] <= _STALENESS_THRESHOLD:
                if len(self.departures[line_key]) > 0:
                    if any((d - now) >= _DEPARTURE_LOWER_BOUND for d in self.departures[line_key]):
                        return True
        return False
