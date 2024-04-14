import datetime
from test.testing import SlideTest

from dateutil import tz

from baseballslide import BaseballSlide

_DEFAULT_CONFIG = {
    'team_name': 'New York Mets',
}

_DEFAULT_GAME_ID_URL = "https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&startDate=2024-04-13&endDate=2024-04-13"
_DEFAULT_GAME_STATS_URL = "https://statsapi.mlb.com/api/v1.1/game/12345/feed/live"


class BaseballSlideTest(SlideTest):

    def setUp(self) -> None:
        super().setUp()
        self.slide = BaseballSlide(self.deps, _DEFAULT_CONFIG)

        # Set a date that matches the expected game ID url.
        test_datetime = datetime.datetime(
            2024, 4, 13, 8, 0, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

    def test_initial_state_not_enabled(self) -> None:

        self.assertEqual(self.slide.game_id_url_callback(),
                         _DEFAULT_GAME_ID_URL)

        # We haven't called the game ID url yet, so we do not know the game ID yet.
        self.assertEqual(self.slide.game_stats_url_callback(), None)
        # Slide has nothing to display.
        self.assertFalse(self.slide.is_enabled())

    def test_after_game_id_fetch(self) -> None:
        self.deps.get_requester().expect(_DEFAULT_GAME_ID_URL,
                                         "baseballslide_game_id.json")
        self.deps.get_requester().start()

        # Ensure we successfully parsed the game ID data.
        self.assertTrue(self.deps.get_requester().last_parse_successful)

        # We should not create a game stats URL, even though we know the ID at this point.
        self.assertEqual(self.slide.game_stats_url_callback(), None)

        # Game ID response specifies that the game starts at 1:40 PM.
        test_datetime = datetime.datetime(
            2024, 4, 13, 13, 40, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        # Url should match the game URL defined in the game ID response.
        self.assertEqual(self.slide.game_stats_url_callback(),
                         _DEFAULT_GAME_STATS_URL)

    def test_game_id_fetch_none_today(self) -> None:
        self.slide = BaseballSlide(self.deps, {
            "team_name": "Team Not in Game ID Response"
        })
        self.deps.get_requester().expect(_DEFAULT_GAME_ID_URL,
                                         "baseballslide_game_id.json")
        self.deps.get_requester().start()

        # Even if no team is found, it should be logged as successful.
        self.assertTrue(self.deps.get_requester().last_parse_successful)

        # Advance past the start of the game, ensure we didn't take a different game by mistake.
        test_datetime = datetime.datetime(
            2024, 4, 13, 13, 40, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)
        self.assertEqual(self.slide.game_stats_url_callback(), None)

    def test_scores_received_before_start(self) -> None:
        # Current time is after the start of the game, even if the live API doesn't mark it as started.
        test_datetime = datetime.datetime(
            2024, 4, 13, 13, 40, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_GAME_ID_URL,
                                         "baseballslide_game_id.json")
        self.deps.get_requester().expect(_DEFAULT_GAME_STATS_URL,
                                         "baseballslide_game_beforestart.json")
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())

    def test_scores_received_during_game(self) -> None:
        # Set current time to after start of game
        test_datetime = datetime.datetime(
            2024, 4, 13, 13, 45, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_GAME_ID_URL,
                                         "baseballslide_game_id.json")
        self.deps.get_requester().expect(_DEFAULT_GAME_STATS_URL,
                                         "baseballslide_game_during.json")
        self.deps.get_requester().start()

        self.assertRenderMatchesGolden(self.slide)

    def test_scores_received_after_end(self) -> None:
        # Set current time to after start of game (exact value doesn't matter)
        test_datetime = datetime.datetime(
            2024, 4, 13, 14, 45, 0, 0, tz.gettz("America/New_York"))
        self.deps.time_source.set(test_datetime)

        self.deps.get_requester().expect(_DEFAULT_GAME_ID_URL,
                                         "baseballslide_game_id.json")
        self.deps.get_requester().expect(_DEFAULT_GAME_STATS_URL,
                                         "baseballslide_game_afterend.json")
        self.deps.get_requester().start()

        self.assertFalse(self.slide.is_enabled())
