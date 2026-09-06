import datetime
import logging
from typing import Dict, List, Optional

import requests
from dateutil import tz
from PIL import Image, ImageDraw  # type: ignore
from json import JSONDecodeError

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import (BLACK, AQUA, WHITE, YELLOW, Align, draw_string, get_string_width, Color)
from glyphs import GlyphSet
from gtfs_realtime_pb2 import FeedMessage  # type: ignore
from requester import Endpoint
from timesource import TimeSource

_REFRESH_INTERVAL = datetime.timedelta(minutes=2)
_STALENESS_THRESHOLD = datetime.timedelta(minutes=10)
_DEPARTURE_LOWER_BOUND = datetime.timedelta(minutes=4)
_MAX_NUM_PREDICTIONS = 2


class NycSubwaySlide(AbstractSlide):
    time_source: TimeSource

    _q_stop_id: str

    departures: Dict[str, List[datetime.datetime]]
    last_updated: Dict[str, datetime.datetime]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()
        self.departures = {}
        self.last_updated = {}
        headers = {"x-api-key": options.get("mta_api_key", "")}

        mta_bus_api_key = options.get("mta_bus_api_key", "")
        self._q_stop_id = options.get("mta_q_stop_id", "")
        b41_stop_id = options.get("mta_b41_stop_id", "")

        deps.get_requester().add_endpoint(Endpoint(
            name="mta_nqrw",
            url="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
            refresh_interval=_REFRESH_INTERVAL,
            parse_callback=self._parse_q,
            error_callback=self._handle_error,
            headers=headers,
        ))
        deps.get_requester().add_endpoint(Endpoint(
            name="mta_b41",
            url=("https://bustime-classic.mta.info/api/siri/stop-monitoring.json?key=%s&version=2&OperatorRef=MTA&MonitoringRef=%s" %
                 (mta_bus_api_key, b41_stop_id)),
            refresh_interval=_REFRESH_INTERVAL,
            parse_callback=self._parse_b41,
            error_callback=self._handle_error
        ))

    def _parse_q(self, response: requests.models.Response) -> bool:
        return self._parse_subway(response, "Q", self._q_stop_id)

    def _parse_subway(self, response: requests.models.Response, expected_line: str, expected_stop: str) -> bool:
        try:
            data = FeedMessage()
            data.ParseFromString(response.content)
        except Exception as e:
            logging.warning("Failed to decode GTFS realtime proto: %s", e)
            return False

        departures = []
        for entity in data.entity:
            line = entity.trip_update.trip.route_id
            if line == expected_line:
                for update in entity.trip_update.stop_time_update:
                    # Ignore updates except at the monitored stop.
                    if update.stop_id == expected_stop:
                        t = datetime.datetime.fromtimestamp(
                            update.departure.time, tz.gettz("America/New_York"))
                        departures.append(t)
        # Departures aren't always given in order, so sort them before storing.
        self.departures[expected_line] = sorted(departures)
        self.last_updated[expected_line] = self.time_source.now()
        return True

    def _parse_b41(self, response: requests.models.Response) -> bool:
        return self._parse_bus(response, "B41")

    def _parse_bus(self, response: requests.models.Response, route: str) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode bus time JSON: %s", response.content)
            return False

        if not "Siri" in data or not "ServiceDelivery" in data["Siri"] or not "StopMonitoringDelivery" in data["Siri"]["ServiceDelivery"]:
            logging.warning(
                "Missing Siri, ServiceDelivery, or StopMonitoringDelivery wrappers in bus data")
            return False

        departures = []
        for smd in data["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"]:
            if "MonitoredStopVisit" in smd:
                for msv in smd["MonitoredStopVisit"]:
                    if "MonitoredVehicleJourney" in msv and "MonitoredCall" in msv["MonitoredVehicleJourney"]:
                        mc = msv["MonitoredVehicleJourney"]["MonitoredCall"]
                        if "ExpectedDepartureTime" in mc:
                            t = datetime.datetime.fromisoformat(
                                mc["ExpectedDepartureTime"])
                            departures.append(t)
                        else:
                            logging.debug(
                                "Got a MC without an ExpectedDepartureTime")
                    else:
                        logging.debug(
                            "Got a MSV without MonitoredVehicleJourney")
            else:
                logging.debug("Got a SMD without a MonitoredStopVisit")

        self.departures[route] = sorted(departures)
        self.last_updated[route] = self.time_source.now()
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
            self._draw_subway_bullet(draw, next_line_y, "Q", YELLOW)
            self._draw_predictions(draw, now, 14, next_line_y, "Q")
            next_line_y += line_height

        if self._has_predictions("B41"):
            self._draw_bus_label(draw, next_line_y, "B41")
            self._draw_predictions(draw, now, get_string_width("B41 ", GlyphSet.FONT_7PX), next_line_y, "B41")
            next_line_y += line_height

    def _get_num_lines(self) -> int:
        return sum([self._has_predictions(line) for line in ["Q", "B41"]])

    def _draw_subway_bullet(self, draw: ImageDraw, y: int, label: str, color: Color) -> None:
        draw.ellipse([(0, y), (10, y+10)], fill=color)
        draw_string(draw, label + " ", 3, y+2,
                    Align.LEFT, GlyphSet.FONT_7PX, BLACK)

    def _draw_bus_label(self, draw: ImageDraw, y: int, label: str) -> None:
        draw_string(draw, label, 0, y+2,
                    Align.LEFT, GlyphSet.FONT_7PX, AQUA)

    def _draw_predictions(self, draw: ImageDraw, now: datetime.datetime, x: int, y: int, line_key: str) -> None:
        departure_strings: List[str] = []
        for departure in self.departures[line_key]:
            diff = (departure - now)
            if diff >= _DEPARTURE_LOWER_BOUND:
                departure_strings.append("%d" % (diff.total_seconds() // 60))
        # Don't show that two different vehicles are departing in the same number of minutes.
        deduped_dpearture_strings = list(dict.fromkeys(departure_strings))
        limited_departure_strings = deduped_dpearture_strings[:_MAX_NUM_PREDICTIONS]
        draw_string(draw, (", ".join(limited_departure_strings)) +
                    " min", x, y+2, Align.LEFT, GlyphSet.FONT_7PX, WHITE)

    def _has_predictions(self, line_key: str) -> bool:
        now = self.time_source.now()
        if line_key in self.last_updated:
            if now - self.last_updated[line_key] <= _STALENESS_THRESHOLD:
                if len(self.departures[line_key]) > 0:
                    if any((d - now) >= _DEPARTURE_LOWER_BOUND for d in self.departures[line_key]):
                        return True
        return False
