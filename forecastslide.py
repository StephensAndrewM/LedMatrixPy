import datetime
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw  # type: ignore

from glyphs import GlyphSet
from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import AQUA, GRAY, WHITE, Align, draw_glyph_by_name, draw_string
from requester import Endpoint
from timesource import TimeSource
from weatherutils import NWS_HEADERS, icon_url_to_weather_glyph

_FORECAST_REFRESH_INTERVAL = datetime.timedelta(minutes=20)
_FORECAST_STALENESS_THRESHOLD = datetime.timedelta(hours=6)


@dataclass
class DailyForecast:
    date: datetime.datetime
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

        forecast_office = options.get("forecast_office", "BOX/69,76")
        deps.get_requester().add_endpoint(Endpoint(
            name="weather_forecast",
            url="https://api.weather.gov/gridpoints/%s/forecast" % forecast_office,
            refresh_interval=_FORECAST_REFRESH_INTERVAL,
            parse_callback=self._parse_forecast,
            error_callback=self._handle_forecast_error,
            headers=NWS_HEADERS,
        ))

    def _parse_forecast(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode forecast JSON: %s", response.content)
            return False

        try:
            update_time = datetime.datetime.fromisoformat(data["updateTime"])
        except ValueError:
            logging.warning(
                "Could not parse forecast update time %s", data["updateTime"])
            return False

        now = self.time_source.now()

        if now - update_time > _FORECAST_STALENESS_THRESHOLD:
            logging.warning(
                "Forecast is too old. Update time is %s", update_time)
            return False

        processed_forecasts: List[DailyForecast] = list()

        if now.hour >= 18:
            # Special-case nightly forecasts if it's evening.
            forecast_tonight = self._get_forecast_with_end_time(
                1, 6, data["periods"])
            if forecast_tonight is None:
                return False
            processed_forecasts.insert(0, DailyForecast(
                date=now,
                icon=icon_url_to_weather_glyph(forecast_tonight.icon),
                high_temp=None,
                low_temp=forecast_tonight.temperature))
        else:
            processed_forecast = self._create_forecast(0, data["periods"])
            if processed_forecast is None:
                return False
            processed_forecasts.insert(0, processed_forecast)

        for i in range(1, int(len(data["periods"])/2)):
            processed_forecast = self._create_forecast(i, data["periods"])
            if processed_forecast is None:
                return False
            processed_forecasts.insert(i, processed_forecast)

        # The data didn't go far enough to display the requested date offset.
        if self.display_date_offset+2 > len(processed_forecasts):
            return False

        # Assign all values at end in case an error returns otherwise.
        self.last_forecast_retrieval = self.time_source.now()
        self.forecasts = processed_forecasts

        return True

    def _create_forecast(self, date_offset: int, periods: List[Dict[str, Any]]) -> Optional[DailyForecast]:
        # End times will always be at 6 AM or 6 PM (regardless of time zone).
        day = self._get_forecast_with_end_time(date_offset, 18, periods)
        night = self._get_forecast_with_end_time(date_offset+1, 6, periods)
        if day is None or night is None:
            return None

        now = self.time_source.now()
        return DailyForecast(date=now + datetime.timedelta(days=date_offset),
                             icon=icon_url_to_weather_glyph(day.icon),
                             high_temp=day.temperature,
                             low_temp=night.temperature)

    def _get_forecast_with_end_time(self, date_offset: int, hour: int,
                                    periods: List[Dict[str, Any]]) -> Optional[ForecastPeriod]:
        now = self.time_source.now()
        end_time = datetime.datetime(
            now.year, now.month, now.day, hour, 0, 0, 0) + datetime.timedelta(days=date_offset)

        for period in periods:
            # Timezone needs to be removed because it can be unpredictable when DST changes.
            forecast_end_time = datetime.datetime.fromisoformat(
                period["endTime"]).replace(tzinfo=None)
            if forecast_end_time == end_time:
                if period["temperature"] is None:
                    return None
                return ForecastPeriod(
                    icon=period["icon"],
                    temperature=period["temperature"]
                )
        logging.warning(
            "Could not find forecast with end time %s", end_time)
        return None

    def _handle_forecast_error(self, response: Optional[requests.models.Response]) -> None:
        # No error handling is needed since we'll display the old values until they expire.
        pass

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        forecast_time_delta = self.time_source.now() - self.last_forecast_retrieval
        if forecast_time_delta <= _FORECAST_STALENESS_THRESHOLD:
            self._draw_forecast(
                draw, 0, 0, self.forecasts[self.display_date_offset])
            self._draw_forecast(
                draw, 0, 16, self.forecasts[self.display_date_offset+1])

            # Show a subtle indicator that this data is mildly stale.
            if (forecast_time_delta > _FORECAST_REFRESH_INTERVAL*2):
                draw.point((83, 31), GRAY)

    def _draw_forecast(self, draw: ImageDraw, x: int, y: int, forecast: DailyForecast) -> None:
        forecast_date = forecast.date.strftime("%a").upper()
        draw_string(draw, forecast_date, x+17, y, Align.LEFT, GlyphSet.FONT_7PX, AQUA)

        if forecast.high_temp is not None:
            forecast_temp = "%d°/%d°" % (forecast.high_temp,
                                         forecast.low_temp)
        else:
            forecast_temp = "%d°" % (forecast.low_temp)
        draw_string(draw, forecast_temp, x+17, y+8, Align.LEFT, GlyphSet.FONT_7PX, WHITE)

        if forecast.icon:
            draw_glyph_by_name(draw, forecast.icon, x, y, GlyphSet.WEATHER, WHITE)
        else:
            draw_string(draw, "?", x+6, y+4, Align.LEFT, GlyphSet.FONT_7PX, GRAY)
