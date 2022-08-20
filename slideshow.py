import logging
import subprocess
import time
from datetime import timedelta
from threading import Timer
from typing import List, Optional

import requests

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

        # Do some initial requests to cover for hardware limitations.
        self._wait_for_network()
        self._sync_system_time()

        # Starts data requesting loop, returning once initial requests are complete.
        self.requester.start()

        self.advance()

    def advance(self) -> None:
        self.advance_timer = Timer(self.advance_interval.seconds, self.advance)
        self.advance_timer.start()

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
        self.redraw_timer.start()

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

        self.display.clear()
        self.requester.stop()

    def freeze(self) -> None:
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()

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


def WelcomeImage() -> PixelGrid:
    grid = PixelGrid()
    grid.draw_string("HELLO!", 64, 2, Align.CENTER, AQUA)
    grid.draw_string("ANDREW'S LED MATRIX", 64, 16, Align.CENTER, YELLOW)
    return grid


def BlankImage() -> PixelGrid:
    return PixelGrid()
