import unittest
from datetime import datetime
from abstractslide import AbstractSlide
from drawing import GREEN, RED, Align, PixelGrid
from test.testing import TestDependencies, compare_to_golden
from transitions import FadeToBlack


class TimeSlideTest(unittest.TestCase):

    def test_render_0p(self) -> None:
        self._test_fade_to_black_at(0, "FadeToBlackTransition0p")

    def test_render_25p(self) -> None:
        self._test_fade_to_black_at(0.25, "FadeToBlackTransition25p")

    def test_render_50p(self) -> None:
        self._test_fade_to_black_at(0.5, "FadeToBlackTransition50p")

    def test_render_75p(self) -> None:
        self._test_fade_to_black_at(0.75, "FadeToBlackTransition75p")

    def test_render_100p(self) -> None:
        self._test_fade_to_black_at(1.0, "FadeToBlackTransition100p")

    def _test_fade_to_black_at(self, progress: float, name: str) -> None:
        g0 = PixelGrid()
        g0.draw_string("A" * 22, 0, 0, Align.LEFT, RED)
        g1 = PixelGrid()
        g1.draw_string("B" * 22, 0, 24, Align.LEFT, GREEN)

        t = FadeToBlack()
        merged_grid = t.merge(progress, g0, g1)
        self.assertTrue(compare_to_golden(name, merged_grid))
