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
    runner_on_first: bool
    runner_on_second: bool
    runner_on_third: bool


class BaseballSlide(AbstractSlide):
    time_source: TimeSource
    team_name: str

    game_id: Optional[str]
    game_start: Optional[datetime.datetime]
    game_started: bool
    game_concluded: bool
    score: Optional[BaseballScore]

    def __init__(self, deps: Dependencies, options: Dict[str, str]) -> None:
        self.time_source = deps.get_time_source()
        self.team_name = options.get('team_name', 'New York Mets')
        self._reset_state()

        deps.get_requester().add_endpoint(Endpoint(
            name="game_id",
            url_callback=self.game_id_url_callback,
            refresh_schedule='0 9 * * *',
            parse_callback=self._parse_game_id,
            error_callback=self._handle_game_id_error,
        ))
        deps.get_requester().add_endpoint(Endpoint(
            name="game_stats",
            url_callback=self.game_stats_url_callback,
            refresh_interval=datetime.timedelta(minutes=5),
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
                        game_date_str = game.get('gameDate', {})
                        # Dates come back using Z suffix for UTC but Python doesn't support this.
                        start_time = datetime.datetime.fromisoformat(
                            game_date_str.replace("Z", "+00:00"))
                    except ValueError:
                        logging.warning(
                            "Could not parse baseball game time %s", game_date_str)
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
        home_team = data.get('gameData', {}).get('teams', {}).get('home', {})
        if 'abbreviation' not in home_team:
            logging.warning(
                "Missing baseball home team abbreviation: %s", home_team)

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

        self.score = BaseballScore(
            home_team_abbr=home_team['abbreviation'],
            home_team_score=home_score,
            away_team_abbr=away_team['abbreviation'],
            away_team_score=away_score,
            inning=line_score['currentInning'],
            top_of_inning=line_score['isTopInning'],
            # TODO read this from the API
            runner_on_first=False,
            runner_on_second=False,
            runner_on_third=False,
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
        self.score = None

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def is_enabled(self) -> bool:
        # TODO show score for a little while after concluding
        return self.game_started and not self.game_concluded and self.score is not None

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)

        if self.score is None:
            return

        self._draw_team_score(
            draw, 0, self.score.away_team_abbr, self.score.away_team_score)
        self._draw_team_score(
            draw, 16, self.score.home_team_abbr, self.score.home_team_score)

        if self.score.top_of_inning:
            inning_icon = "▲"
        else:
            inning_icon = "▼"
        inning_str = "%s%d" % (inning_icon, self.score.inning)

        draw_string(draw, inning_str, 16, 4, Align.CENTER, GlyphSet.FONT_7PX, WHITE)

        self._draw_base(draw, 22, 18, self.score.runner_on_first)
        self._draw_base(draw, 16, 12, self.score.runner_on_second)
        self._draw_base(draw, 10, 18, self.score.runner_on_third)

    def _draw_team_score(self, draw: ImageDraw, y_offset: int, team_abbr: str, score: int) -> None:
        team_color = GRAY
        score_color = GRAY
        # TODO have a more comprehensive list of colors
        if team_abbr == "NYM":
            team_color = ORANGE
            score_color = BLUE

        draw_string(draw, team_abbr, 48, y_offset, Align.CENTER,
                    GlyphSet.FONT_7PX, team_color)
        draw_string(draw, "%d" % score, 48, y_offset+8,
                    Align.CENTER, GlyphSet.FONT_7PX, score_color)

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
