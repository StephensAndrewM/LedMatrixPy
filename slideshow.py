from datetime import datetime, timedelta
from threading import Lock, Timer
from typing import List, Optional

import requests
from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from constants import GRID_WIDTH
from drawing import AQUA, YELLOW, Align, create_slide, draw_string
from transitions import FadeToBlack


class Slideshow:
    advance_interval: Optional[timedelta]
    transition_interval: timedelta
    slides: List[AbstractSlide]

    current_slide_id: int
    current_slide: AbstractSlide
    prev_slide: AbstractSlide
    is_running: bool
    in_transition: bool
    transition_start_time: datetime

    slide_state_lock: Lock
    advance_timer: Optional[Timer]

    def __init__(self, slides: List[AbstractSlide], advance_interval: Optional[timedelta], transition_interval: timedelta) -> None:
        self.advance_interval = advance_interval
        self.transition_interval = transition_interval
        self.slides = slides

        self.slide_state_lock = Lock()
        self.advance_timer = None
        self.is_running = False
        self.in_transition = False

    def start(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        self.current_slide_id = 0
        self.current_slide = self.slides[0]
        self._set_advance_timer()

    def advance(self) -> None:
        self._set_advance_timer()

        next_slide_id = self.current_slide_id+1
        next_slide_id %= len(self.slides)
        while next_slide_id != self.current_slide_id:
            if self.slides[next_slide_id].is_enabled():
                break
            next_slide_id += 1
            next_slide_id %= len(self.slides)

        self.advance_to(next_slide_id)

    def advance_to(self, next_slide_id: int) -> None:
        # No transition needed if we're only displaying one slide.
        if self.current_slide_id == next_slide_id:
            return

        self.slide_state_lock.acquire()

        self.current_slide_id = next_slide_id
        self.prev_slide = self.current_slide
        self.current_slide = self.slides[self.current_slide_id]
        self.in_transition = True
        self.transition_start_time = datetime.now()

        self.slide_state_lock.release()

    def _set_advance_timer(self) -> None:
        self.slide_state_lock.acquire()
        # Schedule the next advance event, if applicable.
        if self.advance_interval is not None:
            self.advance_timer = Timer(
                self.advance_interval.seconds, self.advance)
            self.advance_timer.start()
        self.slide_state_lock.release()

    def draw_frame(self, img: ImageDraw) -> None:
        self.slide_state_lock.acquire()
        if self.in_transition:
            self.draw_transition_frame(img)
        else:
            self.draw_single_frame(img)
        self.slide_state_lock.release()

    def draw_single_frame(self, img: ImageDraw) -> None:
        self.current_slide.draw(img)

    def draw_transition_frame(self, output_img: ImageDraw) -> None:
        # This can be adjusted as more transitions are defined.
        t = FadeToBlack()

        elapsed_time = datetime.now() - self.transition_start_time
        progress = elapsed_time / self.transition_interval
        if progress < 1:
            prev_img = create_slide(self.prev_slide.get_type())
            current_img = create_slide(self.current_slide.get_type())
            self.prev_slide.draw(prev_img)
            self.current_slide.draw(current_img)
            merged_img = t.merge(progress, prev_img, current_img)
            output_img.paste(merged_img)
        else:
            # Switch mode back to regular once transition is complete.
            self.in_transition = False

    def stop(self) -> None:
        if not self.is_running:
            return

        self.is_running = False
        if self.advance_timer is not None:
            self.advance_timer.cancel()
            self.advance_timer.join()

    def freeze(self) -> None:
        if self.is_running and self.advance_timer is not None and self.advance_timer.is_alive():
            self.advance_timer.cancel()
            self.advance_timer.join()

    def unfreeze(self) -> None:
        if self.is_running and self.advance_timer is not None and not self.advance_timer.is_alive():
            self.advance()


class SplitScreenSlide(AbstractSlide):
    static_slide: AbstractSlide
    slideshow: Slideshow

    def __init__(self, static_slide: AbstractSlide, slideshow: Slideshow) -> None:
        self.static_slide = static_slide
        self.slideshow = slideshow

    def slide_type(self) -> SlideType:
        return SlideType.FULL_WIDTH

    def draw(self, img: Image) -> None:
        lhs = create_slide(SlideType.HALF_WIDTH)
        self.static_slide.draw(lhs)
        rhs = create_slide(SlideType.HALF_WIDTH)
        self.slideshow.draw_frame(rhs)
        img.paste(lhs)
        img.paste(rhs, (int(GRID_WIDTH/2), 0))
