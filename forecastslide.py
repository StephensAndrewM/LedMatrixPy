import datetime
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Dict, List, Optional

import requests
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import AQUA, GRAY, WHITE, Align, draw_glyph_by_name, draw_string
from glyphs import GlyphSet
from requester import Endpoint
from timesource import TimeSource
from weatherutils import openweather_object_to_weather_glyph

_FORECAST_REFRESH_INTERVAL = datetime.timedelta(minutes=30)
_FORECAST_STALENESS_THRESHOLD = datetime.timedelta(hours=6)


@dataclass
class DailyForecast:
    date: datetime.date
    icon: Optional[str]
    high_temp: Optional[int]
    low_temp: int


@dataclass
class ForecastPeriod:
    icon: str
    temperature: int


class ForecastSlide(AbstractSlide):
    time_source: TimeSource

    last_forecast_retrieval: datetime.datetime
    forecasts: List[DailyForecast]
    display_date_offset: int

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()

        local_timezone = datetime.datetime.now().astimezone().tzinfo
        self.last_forecast_retrieval = datetime.datetime.min.replace(
            tzinfo=local_timezone)
        self.forecasts = list()
        self.display_date_offset = int(options.get("date_offset", "0"))

        openweather_api_key = options.get("openweather_api_key", "")
        weather_lat = options.get("weather_lat", "")
        weather_lng = options.get("weather_lng", "")
        if openweather_api_key and weather_lat and weather_lng:
            deps.get_requester().add_endpoint(Endpoint(
                name=("weather_current_plus%d" % self.display_date_offset),
                url="https://api.openweathermap.org/data/3.0/onecall?lat=%s&lon=%s&exclude=current,minutely,hourly,alerts&units=imperial&appid=%s" % (
                    weather_lat,
                    weather_lng,
                    openweather_api_key,
                ),
                refresh_interval=_FORECAST_REFRESH_INTERVAL,
                parse_callback=self._parse_forecast,
                error_callback=self._handle_forecast_error,
            ))

    def _parse_forecast(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode forecast JSON: %s", response.content)
            return False

        if not "daily" in data or len(data["daily"]) == 0:
            logging.warning("Missing daily forecasts")
            return False

        forecasts = data["daily"]

        forecast0 = self._find_forecast(forecasts, self.display_date_offset)
        forecast1 = self._find_forecast(
            forecasts, self.display_date_offset + 1)

        if forecast0 and forecast1:
            self.last_forecast_retrieval = self.time_source.now()
            self.forecasts = [forecast0, forecast1]
            return True
        else:
            return False

    def _find_forecast(self, forecasts: List[Any], date_offset: int) -> Optional[DailyForecast]:
        expected_date = (self.time_source.now() +
                         datetime.timedelta(days=date_offset)).date()
        for forecast in forecasts:
            forecast_date = datetime.datetime.fromtimestamp(
                forecast["dt"]).date()
            logging.debug("Comparing %s and %s", forecast_date, expected_date)
            if forecast_date == expected_date:
                return DailyForecast(
                    date=forecast_date,
                    icon=openweather_object_to_weather_glyph(forecast),
                    high_temp=int(forecast["temp"]["day"]),
                    low_temp=int(forecast["temp"]["night"]),
                )
        logging.debug("Did not find a forecast with matching date")
        return None

    def _handle_forecast_error(self, response: Optional[requests.models.Response]) -> None:
        # No error handling is needed since we'll display the old values until they expire.
        pass

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def is_enabled(self) -> bool:
        return self._has_valid_data()

    def draw(self, img: Image) -> None:
        if not self._has_valid_data():
            return

        draw = ImageDraw.Draw(img)
        self._draw_forecast(draw, 0, 0, self.forecasts[0])
        self._draw_forecast(draw, 0, 16, self.forecasts[1])

    def _has_valid_data(self) -> bool:
        # Slide should not be shown if we are missing predictions entirely.
        forecast_time_delta = self.time_source.now() - self.last_forecast_retrieval
        return forecast_time_delta <= _FORECAST_STALENESS_THRESHOLD

    def _draw_forecast(self, draw: ImageDraw, x: int, y: int, forecast: DailyForecast) -> None:
        forecast_date = forecast.date.strftime("%a").upper()
        draw_string(draw, forecast_date, x+17, y,
                    Align.LEFT, GlyphSet.FONT_7PX, AQUA)

        if forecast.high_temp is not None:
            forecast_temp = "%d°/%d°" % (forecast.high_temp,
                                         forecast.low_temp)
        else:
            forecast_temp = "%d°" % (forecast.low_temp)
        draw_string(draw, forecast_temp, x+17, y+8,
                    Align.LEFT, GlyphSet.FONT_7PX, WHITE)

        if forecast.icon:
            draw_glyph_by_name(draw, forecast.icon, x, y,
                               GlyphSet.WEATHER, WHITE)
        else:
            draw_string(draw, "?", x+6, y+4, Align.LEFT,
                        GlyphSet.FONT_7PX, GRAY)
