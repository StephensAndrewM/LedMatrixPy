from test.testing import SlideTest

from PIL import Image, ImageDraw  # type: ignore

from abstractslide import SlideType
from drawing import GREEN, RED, Align, create_slide, draw_string
from glyphs import GlyphSet
from transitions import FadeToBlack


class FadeToBlackTransitionTest(SlideTest):

    def test_0p(self) -> None:
        actual_img = self._test_fade_to_black_at(0)
        self.assertImageMatchesGolden(actual_img)

    def test_25p(self) -> None:
        actual_img = self._test_fade_to_black_at(0.25)
        self.assertImageMatchesGolden(actual_img)

    def test_50p(self) -> None:
        actual_img = self._test_fade_to_black_at(0.5)
        self.assertImageMatchesGolden(actual_img)

    def test_75p(self) -> None:
        actual_img = self._test_fade_to_black_at(0.75)
        self.assertImageMatchesGolden(actual_img)

    def test_100p(self) -> None:
        actual_img = self._test_fade_to_black_at(1.0)
        self.assertImageMatchesGolden(actual_img)

    def _test_fade_to_black_at(self, progress: float) -> Image:
        img0 = create_slide(SlideType.HALF_WIDTH)
        draw_string(ImageDraw.Draw(img0), "A" * 22, 0, 0,
                    Align.LEFT, GlyphSet.FONT_7PX, RED)
        img1 = create_slide(SlideType.HALF_WIDTH)
        draw_string(ImageDraw.Draw(img1), "B" * 22, 0, 24,
                    Align.LEFT, GlyphSet.FONT_7PX, GREEN)

        t = FadeToBlack()
        return t.merge(progress, img0, img1)
