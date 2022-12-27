import logging
import subprocess
import time
from datetime import datetime, timedelta
from threading import Timer
from typing import List, Optional

import requests

from abstractslide import AbstractSlide
from config import Config
from display import Display
from drawing import AQUA, YELLOW, Align, PixelGrid
from requester import Requester
from transitions import FadeToBlack


class Slideshow:
    advance_interval: timedelta
    redraw_interval: timedelta
    display: Display
    requester: Requester
    slides: List[AbstractSlide]

    current_slide_id: int
    current_slide: AbstractSlide
    prev_slide: AbstractSlide
    is_running: bool
    advance_timer: Optional[Timer]
    redraw_timer: Optional[Timer]

    def __init__(self, config: Config, display: Display, requester: Requester, slides: List[AbstractSlide]) -> None:
        advance_seconds = config.get("slide_advance", 15)
        self.advance_interval = timedelta(seconds=advance_seconds)
        transition_millis = config.get("transition_millis", 1000)
        self.transition_interval = timedelta(milliseconds=transition_millis)

        # TODO: Make this configurable per-slide.
        self.redraw_interval = timedelta(seconds=1)
        self.display = display
        self.requester = requester
        self.slides = slides

        self.is_running = False
        self.advance_timer = None
        self.redraw_timer = None
        self.start()

    def start(self) -> None:
        if self.is_running:
            return

        self.current_slide_id = -1

        # Draw the welcome slide while waiting for data
        self.current_slide = WelcomeSlide()
        self.display.draw(self.current_slide.draw())

        # Do some initial requests to cover for hardware limitations.
        self._wait_for_network()
        self._sync_system_time()

        # Starts data requesting loop, returning once initial requests are complete.
        self.requester.start()
        self.is_running = True

        self.advance()

    def advance(self) -> None:
        self.advance_timer = Timer(self.advance_interval.seconds, self.advance)
        self.advance_timer.start()

        if self.redraw_timer is not None:
            self.redraw_timer.cancel()
            self.redraw_timer.join()
            self.redraw_timer = None

        # One slide must always be enabled to prevent an infinite loop.
        while True:
            self.current_slide_id += 1
            self.current_slide_id %= len(self.slides)
            if self.slides[self.current_slide_id].is_enabled():
                break

        self.prev_slide = self.current_slide
        self.current_slide = self.slides[self.current_slide_id]

        # Transition starts and then blocks periodic redraw until complete.
        self.run_transition()

        self.redraw_single()

    def redraw_single(self) -> None:
        self.redraw_timer = Timer(
            self.redraw_interval.seconds, self.redraw_single)
        self.redraw_timer.start()

        grid = self.current_slide.draw()
        self.display.draw(grid)

    def run_transition(self) -> None:
        start_time = datetime.now()
        # This can be adjusted as more transitions are defined.
        t = FadeToBlack()

        while True:
            elapsed_time = datetime.now() - start_time
            progress = elapsed_time / self.transition_interval
            if progress >= 1:
                break
            merged_grid = t.merge(
                progress, self.prev_slide.draw(), self.current_slide.draw())
            self.display.draw(merged_grid)

    def stop(self) -> None:
        if not self.is_running:
            return

        # Cancel timers and ensure that their threads have terminated.
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()
            self.advance_timer = None
        if self.redraw_timer is not None:
            self.redraw_timer.cancel()
            self.redraw_timer.join()
            self.redraw_timer = None

        self.display.clear()
        self.requester.stop()
        self.is_running = False

    def freeze(self) -> None:
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()
            self.advance_timer = None

    def unfreeze(self) -> None:
        if self.advance_timer is not None and not self.advance_timer.isAlive():
            self.advance()

    def _wait_for_network(self) -> None:
        attempts = 1
        while True:
            try:
                response = requests.get(
                    "http://clients3.google.com/generate_204")
                if response.status_code == 204:
                    logging.info(
                        "Internet connection present after %d checks", attempts)
                    return
            except Exception as e:
                logging.debug("Exception while checking for connection: %s", e)
            finally:
                attempts += 1
                time.sleep(5)

    def _sync_system_time(self) -> None:
        p = subprocess.run(["/usr/sbin/ntpdate", "-s", "time.google.com"])
        if p.returncode != 0:
            logging.warning(
                "Failed NTP time synchronization with exit code %d", p.returncode)


def BlankImage() -> PixelGrid:
    return PixelGrid()


class WelcomeSlide(AbstractSlide):

    def draw(self) -> PixelGrid:
        grid = PixelGrid()
        grid.draw_string("HELLO!", 64, 2, Align.CENTER, AQUA)
        grid.draw_string("ANDREW'S LED MATRIX", 64, 16, Align.CENTER, YELLOW)
        return grid
