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
from glyphs import GlyphSet
from requester import Endpoint
from timesource import TimeSource
from weatherutils import (NWS_HEADERS, celsius_to_fahrenheit,
                          icon_url_to_weather_glyph)

_OBSERVATIONS_REFRESH_INTERVAL = datetime.timedelta(minutes=5)
_OBSERVATIONS_STALENESS_THRESHOLD = datetime.timedelta(hours=3)


class TimeAndTemperatureSlide(AbstractSlide):
    time_source: TimeSource

    last_observations_retrieval: datetime.datetime
    current_temp: Optional[int]
    current_icon: Optional[str]

    last_air_quality_retrieval: datetime.datetime
    current_aqi: Optional[int]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()

        local_timezone = datetime.datetime.now().astimezone().tzinfo
        self.last_observations_retrieval = datetime.datetime.min.replace(
            tzinfo=local_timezone)
        self.current_temp = None
        self.current_icon = None

        self.last_air_quality_retrieval = datetime.datetime.min.replace(
            tzinfo=local_timezone)
        self.current_aqi = None

        observations_office = options.get("observations_office", "KBOS")
        deps.get_requester().add_endpoint(Endpoint(
            name="weather_observations",
            url="https://api.weather.gov/stations/%s/observations/latest" % observations_office,
            refresh_interval=_OBSERVATIONS_REFRESH_INTERVAL,
            parse_callback=self._parse_observations,
            error_callback=self._handle_observations_error,
            headers=NWS_HEADERS,
        ))

        airnow_zip_code = options.get("airnow_zip_code", "")
        airnow_api_key = options.get("airnow_api_key", "")
        if airnow_zip_code and airnow_api_key:
            deps.get_requester().add_endpoint(Endpoint(
                name="air_quality",
                url="https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=%s&API_KEY=%s" % (
                    airnow_zip_code, airnow_api_key),
                refresh_interval=_OBSERVATIONS_REFRESH_INTERVAL,
                parse_callback=self._parse_air_quality,
                error_callback=self._handle_air_quality_error,
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

        # Get the time at which the observations were reported. This can be a long
        # time in the past even if the request itself is fresh.
        try:
            reported_time = datetime.datetime.fromisoformat(data["timestamp"])
        except ValueError:
            logging.warning(
                "Could not parse observations report time %s", data["timestamp"])
            return False

        observations_time_delta = self.time_source.now() - reported_time
        if observations_time_delta > _OBSERVATIONS_STALENESS_THRESHOLD:
            logging.warning(
                "Received already stale observations (%s old)", observations_time_delta)
            return False

        # Assign all values at end in case an error returns otherwise.
        self.last_observations_retrieval = reported_time
        self.current_temp = int(
            celsius_to_fahrenheit(data["temperature"]["value"]))

        self.current_icon = None
        if "icon" in data:
            icon_url = data["icon"]
            if isinstance(icon_url, str):
                self.current_icon = icon_url_to_weather_glyph(data["icon"])
            else:
                logging.warning("Got icon url that wasn't a string" % icon_url)

        return True

    def _handle_observations_error(self, response: Optional[requests.models.Response]) -> None:
        # No error handling is needed since we'll display the old value until it expires.
        pass

    def _parse_air_quality(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode air quality JSON: %s", response.content)
            return False

        pm25_observation = next(
            (observation for observation in data if observation["ParameterName"] == "PM2.5"), None)
        if pm25_observation is None:
            logging.warning("Air quality data had no PM2.5 observation")
            return False

        self.last_air_quality_retrieval = self.time_source.now()
        self.current_aqi = int(pm25_observation["AQI"])

        return True

    def _handle_air_quality_error(self, response: Optional[requests.models.Response]) -> None:
        # No error handling is needed since we'll display the old value until it expires.
        pass

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        now = self.time_source.now()

        observations_time_delta = self.time_source.now() - self.last_observations_retrieval
        time_y_offset = 0
        if (self.current_temp is not None and observations_time_delta <= _OBSERVATIONS_STALENESS_THRESHOLD):
            if self.current_icon:
                draw_glyph_by_name(draw, self.current_icon,
                                   0, 16, GlyphSet.WEATHER, WHITE)
            else:
                draw_string(draw, "?", 6, 21, Align.LEFT,
                            GlyphSet.FONT_7PX, GRAY)
            draw_string(draw, "%d°" % self.current_temp,
                        18, 21, Align.LEFT, GlyphSet.FONT_7PX, WHITE)

            # Only draw AQI if we also have weather conditions.
            air_quality_time_delta = self.time_source.now() - self.last_air_quality_retrieval
            if (self.current_aqi is not None and air_quality_time_delta <= _OBSERVATIONS_STALENESS_THRESHOLD):
                if self.current_aqi > 100:
                    draw_string(draw, "AQI", 50, 16, Align.CENTER,
                                GlyphSet.FONT_7PX, RED)
                    draw_string(draw, str(self.current_aqi),
                                50, 24, Align.CENTER, GlyphSet.FONT_7PX,    RED)

        else:
            # Push down the date and time if there we don't have current conditions.
            time_y_offset = 8

        date_string = now.strftime("%a %b %-d").upper()
        draw_string(draw, date_string, 0, time_y_offset+0,
                    Align.LEFT, GlyphSet.FONT_7PX, YELLOW)
        time_string = now.strftime("%-I:%M %p")
        draw_string(draw, time_string, 0, time_y_offset+8,
                    Align.LEFT, GlyphSet.FONT_7PX, YELLOW)
