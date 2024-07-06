import datetime
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Dict, Optional

import requests
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import AQUA, GRAY, WHITE, Align, Color, draw_string
from glyphs import GlyphSet
from requester import Endpoint
from timesource import TimeSource
from timeutils import parse_utc_datetime

_SCOREBOARD_URL = 'https://cdn.wnba.com/static/json/liveData/scoreboard/todaysScoreboard_10.json'


@dataclass
class BasketballScore:
    home_team_abbr: str
    home_team_score: int
    away_team_abbr: str
    away_team_score: int
    status_text: str


class BasketballSlide(AbstractSlide):
    time_source: TimeSource
    team_code: str

    game_start_time: Optional[datetime.datetime]
    game_concluded: bool
    score: Optional[BasketballScore]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()
        self.team_code = options.get('team_code', 'NYL')
        self._reset_state()

        deps.get_requester().add_endpoint(Endpoint(
            name="wnba_game_start_time",
            url=_SCOREBOARD_URL,
            refresh_schedule='0 9 * * *',
            parse_callback=self._parse_game_start_time,
            error_callback=self._handle_game_start_time_error,
        ))
        deps.get_requester().add_endpoint(Endpoint(
            name="wnba_game_stats",
            url_callback=self.game_stats_url_callback,
            refresh_interval=datetime.timedelta(minutes=1),
            parse_callback=self._parse_game_stats,
            error_callback=self._handle_game_stats_error,
        ))

    def _parse_game_start_time(self, response: requests.models.Response) -> bool:
        self._reset_state()

        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode basketball game ID JSON: %s", response.content)
            return False

        game = self._find_game_in_scoreboard(data)
        if game is None:
            logging.debug(
                "No basketball game found in game start parsing matching team code")
            return True

        try:
            game_time_str = game.get("gameTimeUTC", "")
            start_time = parse_utc_datetime(game_time_str)
        except ValueError as e:
            logging.warning(
                "Could not parse basketball game time: %s, %s", game_time_str, e)
            return False

        self.game_start_time = start_time
        self.game_concluded = False
        return True

    def _handle_game_start_time_error(self, response: Optional[requests.models.Response]) -> None:
        self._reset_state()

    def game_stats_url_callback(self) -> Optional[str]:
        if self.game_start_time is None:
            logging.debug(
                "No game stats URL generated because no game start time.")
            return None

        if self.time_source.now() < self.game_start_time:
            logging.debug("No game stats URL generated because start time %s is before current time %s.",
                          self.game_start_time, self.time_source.now())
            return None

        if self.game_concluded:
            logging.debug(
                "No game stats URL generated because game has concluded.")
            return None

        # The URL is static but we want to avoid requesting when a game isn't in progress.
        return _SCOREBOARD_URL

    def _parse_game_stats(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode basketball game stats JSON: %s", response.content)
            return False

        game = self._find_game_in_scoreboard(data)
        if game is None:
            # This function shouldn't have been called if the game couldn't be found, so here it's an error.
            logging.warning(
                "No basketball game found in game stats parsing matching team code")
            return False

        status = game.get("gameStatus", 0)
        # 1 = Game has not yet started.
        if status == 1:
            self.game_concluded = False
        # 2 = Game in progress.
        elif status == 2:
            self.game_concluded = False
        # 3 = Game has ended.
        elif status == 3:
            self.game_concluded = True
        else:
            logging.warning("Unknown basketball status %d", status)
            self.game_concluded = True
            return False

        status_text = game.get("gameStatusText", "").upper()
        if not status_text:
            logging.warning("Failed to get game status text")
            return False

        home_team_abbr = game.get("homeTeam", {}).get("teamTricode", "")
        if not home_team_abbr:
            logging.warning("Failed to get home team tricode")
            return False
        home_team_score = game.get("homeTeam", {}).get("score", -1)
        if home_team_score < 0:
            logging.warning("Failed to get home team score")
            return False

        away_team_abbr = game.get("awayTeam", {}).get("teamTricode", "")
        if not away_team_abbr:
            logging.warning("Failed to get away team tricode")
            return False
        away_team_score = game.get("awayTeam", {}).get("score", -1)
        if away_team_score < 0:
            logging.warning("Failed to get away team score")
            return False

        self.score = BasketballScore(
            home_team_abbr=home_team_abbr,
            home_team_score=home_team_score,
            away_team_abbr=away_team_abbr,
            away_team_score=away_team_score,
            status_text=status_text,
        )
        return True

    def _handle_game_stats_error(self, response: Optional[requests.models.Response]) -> None:
        # Don't reset other data about the game, just the live scores.
        self.score = None

    def _find_game_in_scoreboard(self, data: Any) -> Any:
        for game in data.get("scoreboard", {}).get("games", []):
            if (game.get("homeTeam", {}).get("teamTricode", "") == self.team_code
                    or game.get("awayTeam", {}).get("teamTricode", "") == self.team_code):
                return game
        return None

    def _reset_state(self) -> None:
        self.game_start_time = None
        self.game_concluded = False
        self.score = None

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def is_enabled(self) -> bool:
        # Approximate a game as ~3h (upper bound) with 1 hour to show the result.
        game_end_within_threshold = self.game_start_time is not None and (
            self.time_source.now() - self.game_start_time) < datetime.timedelta(hours=4)
        return self.score is not None and (not self.game_concluded or game_end_within_threshold)

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)

        if self.score is None:
            return

        self._draw_team_score(
            draw, 0, self.score.away_team_abbr, self.score.away_team_score)
        self._draw_team_score(
            draw, 16, self.score.home_team_abbr, self.score.home_team_score)

        if self.game_concluded:
            self._draw_status(draw, "FINAL", GRAY)
        else:
            self._draw_status(draw, self.score.status_text, WHITE)

    def _draw_team_score(self, draw: ImageDraw, y_offset: int, team_abbr: str, score: int) -> None:
        if team_abbr == "NYL":
            color = AQUA
        else:
            color = WHITE

        draw_string(draw, team_abbr, 16, y_offset, Align.CENTER,
                    GlyphSet.FONT_7PX, color)
        draw_string(draw, "%d" % score, 16, y_offset+8,
                    Align.CENTER, GlyphSet.FONT_7PX, color)

    def _draw_status(self, draw: ImageDraw, text: str, c: Color) -> None:
        lines = text.split(" ")
        start_y = 12 - ((len(lines)-1)*4)
        for (i, line) in enumerate(lines):
            draw_string(draw, line, 48, start_y+(i*8),
                        Align.CENTER, GlyphSet.FONT_7PX, c)
