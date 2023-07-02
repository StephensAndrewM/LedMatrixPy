import logging
import re
from typing import Optional

NWS_HEADERS = {
    "User-Agent": "https://github.com/stephensandrewm/LedMatrixPy",
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


def icon_url_to_weather_glyph(url: str) -> Optional[str]:
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


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 1.8) + 32
