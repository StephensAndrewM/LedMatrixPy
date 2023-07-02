import unittest
from test.testing import compare_to_golden

from PIL import ImageDraw  # type: ignore

from abstractslide import SlideType
from drawing import GREEN, RED, Align, create_slide, draw_string
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
        img0 = create_slide(SlideType.HALF_WIDTH)
        draw_string(ImageDraw.Draw(img0), "A" * 22, 0, 0, Align.LEFT, RED)
        img1 = create_slide(SlideType.HALF_WIDTH)
        draw_string(ImageDraw.Draw(img1), "B" * 22, 0, 24, Align.LEFT, GREEN)

        t = FadeToBlack()
        merged_grid = t.merge(progress, img0, img1)
        self.assertTrue(compare_to_golden(name, merged_grid))
