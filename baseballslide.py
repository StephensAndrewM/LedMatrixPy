import datetime
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Dict, Optional

import requests
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import BLUE, GRAY, ORANGE, WHITE, YELLOW, Align, draw_string
from glyphs import GlyphSet
from requester import Endpoint
from timesource import TimeSource


@dataclass
class BaseballScore:
    home_team_abbr: str
    home_team_score: int
    away_team_abbr: str
    away_team_score: int
    inning: int
    top_of_inning: bool
    outs: int
    runner_on_first: bool
    runner_on_second: bool
    runner_on_third: bool


class BaseballSlide(AbstractSlide):
    time_source: TimeSource
    team_name: str
    team_code: str

    game_id: Optional[str]
    game_start: Optional[datetime.datetime]
    game_started: bool
    game_concluded: bool
    last_event_time: Optional[datetime.datetime]
    score: Optional[BaseballScore]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()
        self.team_name = options.get('team_name', 'New York Mets')
        self.team_code = options.get('team_code', 'NYM')
        self._reset_state()

        deps.get_requester().add_endpoint(Endpoint(
            name="mlb_game_id",
            url_callback=self.game_id_url_callback,
            refresh_schedule='0 9 * * *',
            parse_callback=self._parse_game_id,
            error_callback=self._handle_game_id_error,
        ))
        deps.get_requester().add_endpoint(Endpoint(
            name="mlb_game_stats",
            url_callback=self.game_stats_url_callback,
            refresh_interval=datetime.timedelta(minutes=1),
            parse_callback=self._parse_game_stats,
            error_callback=self._handle_game_stats_error,
        ))

    def game_id_url_callback(self) -> Optional[str]:
        today_str = self.time_source.now().strftime("%Y-%m-%d")
        return ("https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&startDate=%s&endDate=%s" % (today_str, today_str))

    def _parse_game_id(self, response: requests.models.Response) -> bool:
        self._reset_state()

        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode baseball game ID JSON: %s", response.content)
            return False

        for date in data.get('dates', []):
            games = date.get('games', [])
            for game in games:
                if (game.get('teams', {}).get('home', {}).get('team', {}).get('name', {}) == self.team_name
                        or game.get('teams', {}).get('away', {}).get('team', {}).get('name', {}) == self.team_name):
                    try:
                        game_date_str = game.get('gameDate', '')
                        start_time = self._parse_datetime(game_date_str)
                    except ValueError:
                        logging.warning(
                            "Could not parse baseball game time: %s", game_date_str)
                        return False

                    self.game_id = game['link']
                    self.game_start = start_time
                    self.game_concluded = False
                    # Return at first match. There should never be more than one match. Maybe double-headers?
                    return True

            logging.debug("Found %d games in but none for %s ",
                          len(games), self.team_name)

        # A valid response may contain no games for the team, so return anyway to avoid re-requesting.
        return True

    def _handle_game_id_error(self, response: Optional[requests.models.Response]) -> None:
        self._reset_state()

    def game_stats_url_callback(self) -> Optional[str]:
        if self.game_id is None or self.game_start is None:
            logging.debug(
                "No game stats URL generated because no game ID or game start time.")
            return None

        if self.time_source.now() < self.game_start:
            logging.debug("No game stats URL generated because start time %s is before current time %s.",
                          self.game_start, self.time_source.now())
            return None

        if self.game_concluded:
            logging.debug(
                "No game stats URL generated because game has concluded.")
            return None

        # Full url is given when fetching game ID, so we don't need to format it further.
        return "https://statsapi.mlb.com" + self.game_id

    def _parse_game_stats(self, response: requests.models.Response) -> bool:
        try:
            data = response.json()
        except JSONDecodeError:
            logging.warning(
                "Failed to decode baseball game stats JSON: %s", response.content)
            return False

        away_team = data.get('gameData', {}).get('teams', {}).get('away', {})
        if 'abbreviation' not in away_team:
            logging.warning(
                "Missing baseball away team abbreviation: %s", away_team)
            return False
        home_team = data.get('gameData', {}).get('teams', {}).get('home', {})
        if 'abbreviation' not in home_team:
            logging.warning(
                "Missing baseball home team abbreviation: %s", home_team)
            return False

        status = data.get('gameData', {}).get('status', {})
        if 'abstractGameState' not in status:
            logging.warning(
                "Failed to find abstractGameState in baseball game stats. Status: %s", status)
            return False
        if status['abstractGameState'] == 'Preview':
            self.game_started = False
            self.game_concluded = False
        elif status['abstractGameState'] == 'Final':
            self.game_started = True
            self.game_concluded = True
        elif status['abstractGameState'] == 'Live':
            self.game_started = True
            self.game_concluded = False
        else:
            logging.info(
                "Got unexpected abstractGameState in baseball game stats. Status: %s", status)
            self.game_started = False
            self.game_concluded = True

        line_score = data.get('liveData', {}).get('linescore', {})

        if "currentInning" not in line_score:
            logging.warning("Failed to find currentInning in linescore")
            return False
        if "isTopInning" not in line_score:
            logging.warning("Failed to find isTopInning in linescore")
            return False
        home_score = line_score.get('teams', {}).get(
            'home', {}).get('runs', -1)
        if home_score < 0:
            logging.warning("Failed to get score for home team")
            return False
        away_score = line_score.get('teams', {}).get(
            'away', {}).get('runs', -1)
        if away_score < 0:
            logging.warning("Failed to get score for away team")
            return False

        current_play = data.get('liveData', {}).get(
            'plays', {}).get('currentPlay', {})
        outs = current_play.get('count', {}).get('outs', -1)
        if outs < 0:
            logging.warning("Failed to get number of outs from currentPlay")
            return False

        current_play_end_time_str = current_play.get(
            'about', {}).get('endTime', '')
        try:
            self.last_event_time = self._parse_datetime(
                current_play_end_time_str)
        except ValueError:
            logging.warning(
                "Could not parse current play end time: %s", current_play_end_time_str)
            return False

        runner_on_first = 'first' in line_score.get('offense', {})
        runner_on_second = 'second' in line_score.get('offense', {})
        runner_on_third = 'third' in line_score.get('offense', {})

        self.score = BaseballScore(
            home_team_abbr=home_team['abbreviation'],
            home_team_score=home_score,
            away_team_abbr=away_team['abbreviation'],
            away_team_score=away_score,
            inning=line_score['currentInning'],
            top_of_inning=line_score['isTopInning'],
            outs=outs,
            runner_on_first=runner_on_first,
            runner_on_second=runner_on_second,
            runner_on_third=runner_on_third,
        )

        return True

    def _handle_game_stats_error(self, response: Optional[requests.models.Response]) -> None:
        # Don't reset other data about the game, just the live scores.
        self.score = None

    def _reset_state(self) -> None:
        self.game_id = None
        self.game_start = None
        self.game_started = False
        self.game_concluded = True
        self.last_event_time = None
        self.score = None

    # Dates are provided using Z suffix for UTC but Python doesn't support this.
    def _parse_datetime(self, str: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(str.replace("Z", "+00:00"))

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def is_enabled(self) -> bool:
        game_end_within_threshold = self.last_event_time is not None and (
            self.time_source.now() - self.last_event_time) < datetime.timedelta(hours=1)
        return self.game_started and self.score is not None and (not self.game_concluded or game_end_within_threshold)

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)

        if self.score is None:
            return

        self._draw_team_score(
            draw, 0, self.score.away_team_abbr, self.score.away_team_score)
        self._draw_team_score(
            draw, 16, self.score.home_team_abbr, self.score.home_team_score)

        if self.game_concluded:
            draw_string(draw, "FINAL", 48, 12, Align.CENTER,
                        GlyphSet.FONT_7PX, GRAY)
        else:
            if self.score.top_of_inning:
                inning_icon = "▲"
            else:
                inning_icon = "▼"
            inning_str = "%s%d" % (inning_icon, self.score.inning)

            draw_string(draw, inning_str, 48, 16, Align.CENTER,
                        GlyphSet.FONT_7PX, WHITE)
            draw_string(draw, "%d OUT" % self.score.outs, 48, 24, Align.CENTER,
                        GlyphSet.FONT_7PX, WHITE)

            self._draw_base(draw, 48+6, 6, self.score.runner_on_first)
            self._draw_base(draw, 48, 0, self.score.runner_on_second)
            self._draw_base(draw, 48-6, 6, self.score.runner_on_third)

    def _draw_team_score(self, draw: ImageDraw, y_offset: int, team_abbr: str, score: int) -> None:
        if team_abbr == self.team_code:
            color = ORANGE
        else:
            color = WHITE

        draw_string(draw, team_abbr, 16, y_offset, Align.CENTER,
                    GlyphSet.FONT_7PX, color)
        draw_string(draw, "%d" % score, 16, y_offset+8,
                    Align.CENTER, GlyphSet.FONT_7PX, color)

    def _draw_base(self, draw: ImageDraw, origin_x: int, origin_y: int, filled: bool) -> None:
        if filled:
            color = YELLOW
        else:
            color = GRAY

        draw.polygon(
            [(origin_x, origin_y), (origin_x+4, origin_y+4),
             (origin_x, origin_y+8), (origin_x-4, origin_y+4)],
            fill=color,
            outline=None,
        )
