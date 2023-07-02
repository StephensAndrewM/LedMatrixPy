
from datetime import timedelta
from threading import Thread
from typing import List

from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from config import Config
from constants import GRID_WIDTH
from display import Display
from drawing import AQUA, YELLOW, Align, create_slide, draw_string
from requester import Requester
from slideshow import Slideshow


class WelcomeSlide(AbstractSlide):
    def get_type(self) -> SlideType:
        return SlideType.FULL_WIDTH

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        draw_string(draw, "HELLO!", 64, 2, Align.CENTER, AQUA)
        draw_string(draw, "ANDREW'S LED MATRIX", 64, 16, Align.CENTER, YELLOW)


class SplitScreenSlide(AbstractSlide):
    static_slide: AbstractSlide
    slideshow: Slideshow

    def __init__(self, static_slide: AbstractSlide, slideshow: Slideshow) -> None:
        self.static_slide = static_slide
        self.slideshow = slideshow

    def get_type(self) -> SlideType:
        return SlideType.FULL_WIDTH

    def draw(self, img: Image) -> None:
        lhs = create_slide(SlideType.HALF_WIDTH)
        self.static_slide.draw(lhs)
        rhs = create_slide(SlideType.HALF_WIDTH)
        self.slideshow.draw_frame(rhs)
        img.paste(lhs)
        img.paste(rhs, (int(GRID_WIDTH/2), 0))


class Show:
    display: Display
    requester: Requester
    static_slide: AbstractSlide

    inner_slideshow: Slideshow
    split_screen_slide: SplitScreenSlide
    outer_slideshow: Slideshow

    draw_enabled: bool
    draw_thread: Thread

    def __init__(self, config: Config, display: Display, requester: Requester, static_slide: AbstractSlide, rotating_slides: List[AbstractSlide]) -> None:
        self.display = display
        self.requester = requester

        inner_slide_advance = timedelta(
            seconds=config.get("slide_advance", 15))
        transition_interval = timedelta(
            milliseconds=config.get("transition_millis", 1000))
        self.inner_slideshow = Slideshow(
            rotating_slides, inner_slide_advance, transition_interval)
        self.split_screen_slide = SplitScreenSlide(
            static_slide, self.inner_slideshow)

        outer_slides = [WelcomeSlide(), self.split_screen_slide]
        self.outer_slideshow = Slideshow(
            outer_slides, advance_interval=None, transition_interval=transition_interval)

        self.start()

    def start(self) -> None:
        # Enables welcome slide.
        self.outer_slideshow.start()
        self.outer_slideshow.advance_to(0)

        self.draw_enabled = True
        self.draw_thread = Thread(target=self._draw_loop)
        self.draw_thread.start()

    def startup_complete(self) -> None:
        self.requester.start()
        self.inner_slideshow.start()
        self.outer_slideshow.advance_to(1)

    def _draw_loop(self) -> None:
        while self.draw_enabled:
            img = create_slide(SlideType.FULL_WIDTH)
            self.outer_slideshow.draw_frame(img)
            self.display.draw(img)

    def stop(self) -> None:
        if not self.draw_enabled:
            return

        self.draw_enabled = False
        self.outer_slideshow.stop()
        self.inner_slideshow.stop()
        self.requester.stop()

        # Change in draw_enabled should stop the draw thread.
        self.draw_thread.join()
        self.display.clear()

    def advance(self) -> None:
        self.inner_slideshow.advance()

    def freeze(self) -> None:
        self.inner_slideshow.freeze()

    def unfreeze(self) -> None:
        self.inner_slideshow.unfreeze()
