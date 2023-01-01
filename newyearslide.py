import datetime
import math
import random
from typing import List

from PIL import ImageDraw  # type: ignore

from abstractslide import AbstractSlide
from constants import GRID_HEIGHT, GRID_WIDTH
from deps import Dependencies
from drawing import (AQUA, BLUE, GREEN, ORANGE, PURPLE, RED, WHITE, YELLOW,
                     Align, Color, draw_string)
from timesource import TimeSource

_FPS = 30.0
_FIREWORK_COLORS = [AQUA, RED, GREEN, YELLOW, PURPLE, ORANGE]


class Ember:
    color: Color
    x: float
    y: float
    xspeed: float
    yspeed: float

    def __init__(self, c: Color, x: int, y: int, xspeed: float, yspeed: float):
        self.c = c
        self.x = float(x)
        self.y = float(y)
        self.xspeed = xspeed
        self.yspeed = yspeed

    def draw(self, img: ImageDraw) -> None:
        if self.x >= 0 and self.y >= 0 and self.x < GRID_WIDTH and self.y < GRID_HEIGHT:
            img.point((int(round(self.x)), int(round(self.y))), self.c)

    def apply_physics(self) -> None:
        self.x += self.xspeed
        self.y += self.yspeed
        self.yspeed += (2.3 / _FPS)  # gravity
        self.xspeed *= 0.985  # friction

    def is_visible(self) -> bool:
        return self.y < GRID_HEIGHT


class NewYearSlide(AbstractSlide):
    time_source: TimeSource
    target_year: int
    target_datetime: datetime.datetime

    embers: List[Ember]
    next_ember_update: datetime.datetime
    next_firework: datetime.datetime

    def __init__(self, deps: Dependencies):
        self.time_source = deps.get_time_source()
        now = self.time_source.now()
        self.target_year = now.year + 1
        # If the date has rolled over to January, don't change target year yet.
        if now.month == 1:
            self.target_year = now.year

        self.target_datetime = datetime.datetime(
            self.target_year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)

        self.embers = []
        self.next_ember_update = self.time_source.now()
        self.next_firework = self.time_source.now() + datetime.timedelta(seconds=1)

    def draw(self, img: ImageDraw) -> None:
        self._update_embers()
        self._create_firework()

        # Draw embers first so they appear behind the text.
        for ember in self.embers:
            ember.draw(img)

        now = self.time_source.now()
        diff = self.target_datetime - now
        diff_seconds = diff.total_seconds()

        # After midnight
        if diff_seconds < 0:
            draw_string(img, "HAPPY %d!" % self.target_year,
                        64, 12, Align.CENTER, YELLOW)
        else:
            diff_string = '{:02} : {:02} : {:02}'.format(
                int(diff_seconds // 3600), int(diff_seconds % 3600 // 60), int(diff_seconds % 60))

            draw_string(img, diff_string, 64, 6, Align.CENTER, WHITE)
            draw_string(img, "UNTIL %d" % self.target_year,
                        64, 18, Align.CENTER, YELLOW)

    def _update_embers(self) -> None:
        if self.time_source.now() <= self.next_ember_update:
            return

        for ember in self.embers:
            ember.apply_physics()
        # Garbage-collect the embers.
        self.embers = [e for e in self.embers if e.is_visible()]

        self.next_ember_update = self.time_source.now(
        ) + datetime.timedelta(seconds=(1/_FPS))

    def _create_firework(self) -> None:
        if self.time_source.now() <= self.next_firework:
            return

        x = random.choice([*range(8, 32)] + [*range(96, 120)])
        y = random.choice(range(10, 28))
        c = random.choice(_FIREWORK_COLORS)

        new_embers = []

        velocity_base = 0.25
        yspeed_offset = -1.2  # Simulates launch velocity

        new_embers.append(Ember(c, x, y, 0, + yspeed_offset))
        for velocity_multiplier in [1, 2, 3]:
            velocity = velocity_base * velocity_multiplier
            embers_in_ring = 16
            if (velocity <= velocity_base):
                embers_in_ring = 8
            for i in range(0, embers_in_ring):
                angle = (float(i) / (float(embers_in_ring) / 2)) * math.pi
                xspeed = math.sin(angle) * velocity
                yspeed = (math.cos(angle) * velocity) + yspeed_offset
                new_embers.append(Ember(c, x, y, xspeed, yspeed))

        self.embers += new_embers

        seconds_to_next = random.randint(5, 20)
        self.next_firework = self.time_source.now(
        ) + datetime.timedelta(seconds=seconds_to_next)
