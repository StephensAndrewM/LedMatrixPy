import logging
import re
from typing import Any, Optional

# Defines how OpenWeather icon names match to weather glyphs.
# https://openweathermap.org/weather-conditions#How-to-get-icon-URL
_OPENWEATHER_ICON_MAPPING = {
    "01d": "sun",  # clear sky
    "01n": "moon",  # clear sky
    "02d": "cloud_sun",  # few clouds
    "02n": "cloud_moon",  # few clouds
    "03d": "cloud_sun",  # scattered clouds
    "03n": "cloud_moon",  # scattered clouds
    "04d": "clouds",  # broken clouds
    "04n": "clouds",  # broken clouds
    "09d": "rain0",  # shower rain
    "09n": "rain0",  # shower rain
    "10d": "rain1",  # rain
    "10n": "rain1",  # rain
    "11d": "lightning",  # thunderstorm
    "11n": "lightning",  # thunderstorm
    "13d": "snow",  # snow
    "13n": "snow",  # snow
    "50d": "rain0",  # mist
    "50n": "rain0",  # mist
}


def openweather_object_to_weather_glyph(data: Any) -> Optional[str]:
    if ("weather" in data and
        len(data["weather"]) > 0 and
            "icon" in data["weather"][0]):
        return openweather_icon_to_weather_glyph(data["weather"][0]["icon"])
    else:
        return None


def openweather_icon_to_weather_glyph(icon: str) -> Optional[str]:
    if icon in _OPENWEATHER_ICON_MAPPING:
        return _OPENWEATHER_ICON_MAPPING[icon]
    else:
        logging.warning("Openweather icon map did not contain %s", icon)
        return None
