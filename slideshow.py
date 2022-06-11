from datetime import timedelta
from threading import Timer
from typing import List, Optional

from abstractslide import AbstractSlide
from config import Config
from display import Display
from drawing import AQUA, YELLOW, Align, PixelGrid
from requester import Requester


class Slideshow:
    advance_interval: timedelta
    redraw_interval: timedelta
    display: Display
    requester: Requester
    slides: List[AbstractSlide]

    current_slide_id: int
    advance_timer: Optional[Timer]
    redraw_timer: Optional[Timer]

    def __init__(self, config: Config, display: Display, requester: Requester, slides: List[AbstractSlide]) -> None:
        advance_seconds = config.get("slide_advance", 15)
        self.advance_interval = timedelta(seconds=advance_seconds)
        # TODO: Make this configurable per-slide.
        self.redraw_interval = timedelta(seconds=1)
        self.display = display
        self.requester = requester
        self.slides = slides

        self.advance_timer = None
        self.redraw_timer = None
        self.start()

    def start(self) -> None:
        self.current_slide_id = -1

        # Draw the welcome slide while waiting for data
        self.display.draw(WelcomeImage())

        # TODO: Perform system checks

        # Starts data requesting loop, returning once initial requests are complete.
        self.requester.start()

        self.advance()

    def advance(self) -> None:
        self.advance_timer = Timer(self.advance_interval.seconds, self.advance)

        if self.redraw_timer is not None:
            self.redraw_timer.cancel()
            self.redraw_timer.join()

        # One slide must always be enabled to prevent an infinite loop.
        while True:
            self.current_slide_id += 1
            self.current_slide_id %= len(self.slides)
            if self.slides[self.current_slide_id].is_enabled():
                break

        self.redraw()

    def redraw(self) -> None:
        self.redraw_timer = Timer(self.redraw_interval.seconds, self.redraw)

        grid = self.slides[self.current_slide_id].draw()
        self.display.draw(grid)

    def stop(self) -> None:
        # Cancel timers and ensure that their threads have terminated.
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()
        if self.redraw_timer is not None:
            self.redraw_timer.cancel()
            self.redraw_timer.join()

    def freeze(self) -> None:
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()

    def unfreeze(self) -> None:
        if self.advance_timer is not None and not self.advance_timer.isAlive():
            self.advance()


def WelcomeImage() -> PixelGrid:
    grid = PixelGrid()
    grid.draw_string("HELLO!", 64, 2, Align.CENTER, AQUA)
    grid.draw_string("ANDREW'S LED MATRIX", 64, 16, Align.CENTER, YELLOW)
    return grid


def BlankImage() -> PixelGrid:
    return PixelGrid()
