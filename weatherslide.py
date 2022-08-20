import datetime
import logging
import re
from dataclasses import dataclass
from distutils.log import error
from json import JSONDecodeError
from time import tzname
from typing import Any, Dict, List, Optional

import requests

from abstractslide import AbstractSlide
from deps import Dependencies
from drawing import RED, WHITE, YELLOW, Align, Color, PixelGrid
from requester import Endpoint
from timesource import TimeSource

_NWS_HEADERS = {
    "User-Agent": "https://github.com/stephensandrewm/LedMatrix",
    "Accept": "application/ld+json",
}

# Defines how NWS icon names map to weather glyphs
# Based on https://api.weather.gov/icons
_ICON_MAPPING = {
    "day/skc":         "sun",             # Fair/clear
    "night/skc":       "moon",            # Fair/clear
    "day/few":         "cloud_sun",       # A few clouds
    "night/few":       "cloud_moon",      # A few clouds
    "day/sct":         "cloud_sun",       # Partly cloudy
    "night/sct":       "cloud_moon",      # Partly cloudy
    "bkn":             "clouds",          # Mostly cloudy
    "ovc":             "clouds",          # Overcast
    "day/wind_skc":    "sun",             # Fair/clear and windy
    "night/wind_skc":  "moon",            # Fair/clear and windy
    "day/wind_few":    "cloud_wind_sun",  # A few clouds and windy
    "night/wind_few":  "cloud_wind_moon",  # A few clouds and windy
    "day/wind_sct":    "cloud_wind_sun",  # Partly cloudy and windy
    "night/wind_sct":  "cloud_wind_moon",  # Partly cloudy and windy
    "wind_bkn":        "cloud_wind",      # Mostly cloudy and windy
    "wind_ovc":        "cloud_wind",      # Overcast and windy
    "snow":            "snow",            # Snow
    "rain_snow":       "rain_snow",       # Rain/snow
    "rain_sleet":      "rain_snow",       # Rain/sleet
    "snow_sleet":      "rain_snow",       # Snow/sleet
    "fzra":            "rain1",           # Freezing rain
    "rain_fzra":       "rain1",           # Rain/freezing rain
    "snow_fzra":       "rain_snow",       # Freezing rain/snow
    "sleet":           "rain1",           # Sleet
    "rain":            "rain1",           # Rain
    "rain_showers":    "rain0",           # Rain showers (high cloud cover)
    "rain_showers_hi": "rain0",           # Rain showers (low cloud cover)
    "tsra":            "lightning",       # Thunderstorm (high cloud cover)
    "tsra_sct":        "lightning",       # Thunderstorm (med cloud cover)
    "tsra_hi":         "lightning",       # Thunderstorm (low cloud cover)
    "blizzard":        "snow",            # Blizzard
    "fog":             "cloud",           # Fog/mist
}


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


class WeatherSlide(AbstractSlide):
    time_source: TimeSource

    current_temp: Optional[int]
    current_icon: Optional[str]

    forecast1: Optional[DailyForecast]
    forecast2: Optional[DailyForecast]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()

        self.current_temp = None
        self.current_icon = None
        self.forecast1 = None
        self.forecast2 = None

        observations_office = options.get("observations_office", "KBOS")
        deps.get_requester().add_endpoint(Endpoint(
            name="weather_observations",
            url="https://api.weather.gov/stations/%s/observations/latest" % observations_office,
            refresh_interval=datetime.timedelta(minutes=5),
            parse_callback=self.parse_observations,
            error_callback=self.handle_observations_error,
            headers=_NWS_HEADERS,
        ))

        forecast_office = options.get("forecast_office", "BOX/69,76")
        deps.get_requester().add_endpoint(Endpoint(
            name="weather_forecast",
            url="https://api.weather.gov/gridpoints/%s/forecast" % forecast_office,
            refresh_interval=datetime.timedelta(minutes=20),
            parse_callback=self.parse_forecast,
            error_callback=self.handle_forecast_error,
            headers=_NWS_HEADERS,
        ))

    def parse_observations(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode observations JSON: %s", response.content)
            return False

        if not "temperature" in data or data["temperature"]["value"] is None:
            logging.debug("Forecast contains null temperature")
            return False

        self.current_temp = int(
            self._celsius_to_fahrenheit(data["temperature"]["value"]))
        self.current_icon = self._icon_url_to_weather_glyph(data["icon"])

        return True

    def handle_observations_error(self, response: requests.models.Response) -> None:
        self.current_temp = None
        self.current_icon = None

    def parse_forecast(self, response: requests.models.Response) -> bool:
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

        if now - update_time > datetime.timedelta(hours=6):
            logging.warning(
                "Forecast is too old. Update time is %s", update_time)
            return False

        forecast_tonight = self._get_forecast_with_end_time(
            1, 6, data["periods"])
        if forecast_tonight is None:
            return False

        if now.hour < 18:
            forecast_today = self._get_forecast_with_end_time(
                0, 18, data["periods"])
            if forecast_today is None:
                return False

            self.forecast1 = DailyForecast(
                date=now,
                icon=self._icon_url_to_weather_glyph(forecast_today.icon),
                high_temp=forecast_today.temperature,
                low_temp=forecast_tonight.temperature)

        else:
            self.forecast1 = DailyForecast(
                date=now,
                icon=self._icon_url_to_weather_glyph(forecast_tonight.icon),
                high_temp=None,
                low_temp=forecast_tonight.temperature)

        forecast_tomorrow = self._get_forecast_with_end_time(
            1, 18, data["periods"])
        forecast_tomorrow_night = self._get_forecast_with_end_time(
            2, 6, data["periods"])
        if forecast_tomorrow is None or forecast_tomorrow_night is None:
            return False

        self.forecast2 = DailyForecast(
            date=now + datetime.timedelta(days=1),
            icon=self._icon_url_to_weather_glyph(forecast_tomorrow.icon),
            high_temp=forecast_tomorrow.temperature,
            low_temp=forecast_tomorrow_night.temperature
        )

        return True

    def _get_forecast_with_end_time(self, date_offset: int, hour: int, periods: List[Dict[str, Any]]) -> Optional[ForecastPeriod]:
        now = self.time_source.now()
        local_timezone = now.astimezone().tzinfo
        end_time = datetime.datetime(
            now.year, now.month, now.day + date_offset, hour, 0, 0, 0, local_timezone)

        for period in periods:
            forecast_end_time = datetime.datetime.fromisoformat(
                period["endTime"])
            if forecast_end_time == end_time:
                if period["temperature"] is None:
                    return None
                return ForecastPeriod(
                    icon=period["icon"],
                    temperature=period["temperature"]
                )
        logging.warning(
            "Could not find forecast with start time %s", end_time)
        return None

    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        return (celsius * 1.8) + 32

    def _icon_url_to_weather_glyph(self, url: str) -> Optional[str]:
        m = re.search(r'\/icons\/land\/([^\/]+\/([a-z_]+))', url)
        if m is None or len(m.groups()) < 2:
            logging.warning("Could not extract icon from URL %s", url)
            return None
        nws_icon_with_time_of_day = m.groups()[0]
        nws_icon = m.groups()[1]

        # Icon could be defined using one of two patterns. Try both
        if nws_icon_with_time_of_day in _ICON_MAPPING:
            return _ICON_MAPPING[nws_icon_with_time_of_day]
        elif nws_icon in _ICON_MAPPING:
            return _ICON_MAPPING[nws_icon]
        else:
            logging.warning("Weather icon map did not contain %s", nws_icon)
            return None

    def handle_forecast_error(self, response: requests.models.Response) -> None:
        self.forecast1 = None
        self.forecast2 = None

    def draw(self) -> PixelGrid:
        grid = PixelGrid()

        if self.current_temp is None and self.forecast1 is None:
            grid.draw_error("WEATHER", "NO DATA")
            return grid

        if self.current_temp is None:
            grid.draw_string("NOW", 21, 0, Align.CENTER, YELLOW)
            grid.draw_string("?", 21, 16, Align.CENTER, RED)
        else:
            self._draw_weather_box(grid, 21, "NOW", YELLOW, "%d°" %
                                   self.current_temp, self.current_icon)

        if self.forecast1 is not None and self.forecast2 is not None:
            self._draw_forecast(grid, 63, self.forecast1)
            self._draw_forecast(grid, 105, self.forecast2)
        else:
            grid.draw_string("FORECAST", 86, 8, Align.CENTER, RED)
            grid.draw_string("MISSING", 86, 16, Align.CENTER, RED)

        return grid

    def _draw_forecast(self, grid: PixelGrid, x: int, forecast: DailyForecast) -> None:
        forecast_date = forecast.date.strftime("%a").upper()
        if forecast.high_temp is not None:
            forecast_temp = "%d°/%d°" % (forecast.high_temp,
                                       forecast.low_temp)
        else:
            forecast_temp = "%d°" % (forecast.low_temp)
        self._draw_weather_box(
            grid, x, forecast_date, WHITE, forecast_temp, forecast.icon)

    def _draw_weather_box(self, grid: PixelGrid, x: int, date: str, date_color: Color, temperature: str, icon: Optional[str]) -> None:
        grid.draw_string(temperature, x, 0, Align.CENTER, WHITE)
        if icon:
            grid.draw_glyph_by_name(icon, x-8, 8, WHITE)
        grid.draw_string(date, x, 24, Align.CENTER, date_color)
