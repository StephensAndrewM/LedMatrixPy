import datetime
from test.testing import SlideTest

from dateutil import tz

from basketballslide import BasketballSlide

_DEFAULT_CONFIG = {
    'team_code': 'NYL',
}
_SCOREBOARD_URL = 'https://cdn.wnba.com/static/json/liveData/scoreboard/todaysScoreboard_10.json'


class BasketballSlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        self.slide = BasketballSlide(self.deps, _DEFAULT_CONFIG)

        test_datetime = datetime.datetime(
            2024, 4, 13, 8, 0, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

    def test_initial_state_not_enabled(self) -> None:
        # We haven't called the game start url yet, so we do not know the start time yet.
        self.assertEqual(self.slide.game_stats_url_callback(), None)
        # Slide has nothing to display.
        self.assertFalse(self.slide.is_enabled())

    def test_fetching_begins_after_game_starts(self) -> None:
        self.deps.get_requester().expect(_SCOREBOARD_URL,
                                         "basketballslide_game_later_in_day.json")
        self.deps.get_requester().start()

        # Ensure we successfully parsed the game start data.
        self.assertTrue(self.deps.get_requester().last_parse_successful)

        # We should not create a game stats URL, even though we know the start time at this point.
        self.assertEqual(self.slide.game_stats_url_callback(), None)

        # Test data specifies that the game starts at 4:00 PM.
        test_datetime = datetime.datetime(
            2024, 4, 13, 16, 1, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        # Now we should be requesting data for the game.
        self.assertEqual(self.slide.game_stats_url_callback(), _SCOREBOARD_URL)

    def test_game_start_fetch_no_games(self) -> None:
        self.slide = BasketballSlide(self.deps, {
            "team_code": "Team Not in Game ID Response"
        })
        self.deps.get_requester().expect(_SCOREBOARD_URL,
                                         "basketballslide_game_later_in_day.json")
        self.deps.get_requester().start()

        # Even if no team is found, it should be logged as successful.
        self.assertTrue(self.deps.get_requester().last_parse_successful)
        self.assertFalse(self.slide.is_enabled())

        # Advance past the start of the game, ensure we didn't take a different game by mistake.
        test_datetime = datetime.datetime(
            2024, 4, 13, 16, 1, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)
        self.assertEqual(self.slide.game_stats_url_callback(), None)

    def test_scores_received_during_game(self) -> None:
        # Set current time to after start of game.
        test_datetime = datetime.datetime(
            2024, 4, 13, 16, 1, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_SCOREBOARD_URL,
                                         "basketballslide_game_in_progress.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_scores_received_soon_after_end(self) -> None:
        # Set current time to after end of game (3h after game start).
        test_datetime = datetime.datetime(
            2024, 4, 13, 19, 10, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_SCOREBOARD_URL,
                                         "basketballslide_game_finished.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_scores_received_long_after_end(self) -> None:
        # Set current time to after end of game (4h after game start).
        test_datetime = datetime.datetime(
            2024, 4, 13, 20, 30, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_SCOREBOARD_URL,
                                         "basketballslide_game_finished.json")
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())
