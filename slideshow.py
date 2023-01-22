import logging
import subprocess
import time
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock, Thread, Timer
from typing import List, Optional

import requests
from PIL import ImageDraw  # type: ignore

from abstractslide import AbstractSlide
from config import Config
from display import Display
from drawing import AQUA, YELLOW, Align, default_image, draw_string
from requester import Requester
from transitions import FadeToBlack


class DrawMode(Enum):
    NONE = 0
    SINGLE = 1
    TRANSITION = 2


class Slideshow:
    advance_interval: timedelta
    display: Display
    requester: Requester
    slides: List[AbstractSlide]

    current_slide_id: int
    current_slide: AbstractSlide
    prev_slide: AbstractSlide
    is_running: bool
    draw_mode: DrawMode
    transition_start_time: datetime
    slide_state_lock: Lock
    draw_thread: Thread
    advance_timer: Optional[Timer]

    def __init__(self, config: Config, display: Display, requester: Requester, slides: List[AbstractSlide]) -> None:
        advance_seconds = config.get("slide_advance", 15)
        self.advance_interval = timedelta(seconds=advance_seconds)
        transition_millis = config.get("transition_millis", 1000)
        self.transition_interval = timedelta(milliseconds=transition_millis)

        self.display = display
        self.requester = requester
        self.slides = slides

        self.is_running = False
        self.draw_mode = DrawMode.SINGLE
        self.slide_state_lock = Lock()
        self.advance_timer = None

        self.start()

    def start(self) -> None:
        if self.is_running:
            return

        self.current_slide_id = -1

        # Draw the welcome slide while waiting for data
        self.current_slide = WelcomeSlide()
        self.draw_single()

        # Do some initial requests to cover for hardware limitations.
        self._wait_for_network()
        self._sync_system_time()

        # Starts data requesting loop, returning once initial requests are complete.
        self.requester.start()
        self.is_running = True

        self.advance()

        self.draw_thread = Thread(target=self.draw_loop)
        self.draw_thread.start()

    def draw_loop(self) -> None:
        while True:
            self.slide_state_lock.acquire()
            if self.draw_mode == DrawMode.SINGLE:
                self.draw_single()
            elif self.draw_mode == DrawMode.TRANSITION:
                self.draw_transition()
            else:
                self.display.clear()
                self.slide_state_lock.release()
                return
            self.slide_state_lock.release()

    def advance(self) -> None:
        self.slide_state_lock.acquire()

        # Schedule the next advance event.
        self.advance_timer = Timer(self.advance_interval.seconds, self.advance)
        self.advance_timer.start()

        # One slide must always be enabled to prevent an infinite loop.
        next_slide_id = self.current_slide_id
        while True:
            next_slide_id += 1
            next_slide_id %= len(self.slides)
            if self.slides[next_slide_id].is_enabled():
                break

        # No transition needed if we're only displaying one slide.
        if self.current_slide_id == next_slide_id:
            self.slide_state_lock.release()
            return

        self.current_slide_id = next_slide_id
        self.prev_slide = self.current_slide
        self.current_slide = self.slides[self.current_slide_id]

        self.draw_mode = DrawMode.TRANSITION
        self.transition_start_time = datetime.now()
        self.slide_state_lock.release()

    def draw_single(self) -> None:
        img = default_image()
        self.current_slide.draw(ImageDraw.Draw(img))
        self.display.draw(img)

    def draw_transition(self) -> None:
        # This can be adjusted as more transitions are defined.
        t = FadeToBlack()

        elapsed_time = datetime.now() - self.transition_start_time
        progress = elapsed_time / self.transition_interval
        if progress < 1:
            prev_img = default_image()
            current_img = default_image()
            self.prev_slide.draw(ImageDraw.Draw(prev_img))
            self.current_slide.draw(ImageDraw.Draw(current_img))
            merged_grid = t.merge(progress, prev_img, current_img)
            self.display.draw(merged_grid)
        else:
            # Switch mode back to regular once transition is complete.
            self.draw_mode = DrawMode.SINGLE

    def stop(self) -> None:
        if not self.is_running:
            return

        # Cancel timers and ensure that their threads have terminated.
        self.slide_state_lock.acquire()
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()
            self.advance_timer = None

        # Stops the main drawing loop.
        self.draw_mode = DrawMode.NONE
        self.slide_state_lock.release()
        self.draw_thread.join()

        self.requester.stop()
        self.is_running = False

    def freeze(self) -> None:
        self.slide_state_lock.acquire()
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()
            self.advance_timer = None
        self.slide_state_lock.release()

    def unfreeze(self) -> None:
        if self.advance_timer is None:
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


class WelcomeSlide(AbstractSlide):

    def draw(self, img: ImageDraw) -> None:
        draw_string(img, "HELLO!", 64, 2, Align.CENTER, AQUA)
        draw_string(img, "ANDREW'S LED MATRIX", 64, 16, Align.CENTER, YELLOW)
