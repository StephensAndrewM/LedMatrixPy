import datetime
from typing import List, Tuple

from PIL import Image, ImageDraw  # type: ignore

from abstractslide import AbstractSlide, SlideType
from deps import Dependencies
from drawing import (AQUA, BLUE, GREEN, RED, YELLOW, Align, draw_string,
                     get_string_width)
from timesource import TimeSource
from glyphs import GlyphSet

# Define the tree body as a set of tuples setting row X offset and width.
_TREE_SHAPE = [
    (10, 1),
    (9, 3),
    (9, 3),
    (8, 5),
    (8, 5),
    (8, 5),
    (7, 7),
    (7, 7),
    (6, 9),
    (6, 9),
    (6, 9),
    (5, 11),
    (5, 11),
    (4, 13),
    (4, 13),
    (4, 13),
    (3, 15),
    (3, 15),
    (2, 17),
    (2, 17),
    (2, 17),
    (1, 19),
    (1, 19),
    (0, 21),
    (0, 21),
]

_TREE_LIGHTS = [
    (9, 3),
    (12, 5),
    (7, 6),
    (9, 8),
    (12, 10),
    (15, 11),
    (5, 11),
    (8, 13),
    (12, 15),
    (14, 16),
    (17, 17),
    (4, 15),
    (6, 17),
    (8, 19),
    (11, 20),
    (14, 21),
    (17, 22),
    (2, 19),
    (4, 21),
    (7, 23),
    (11, 24),
]


class ChristmasSlide(AbstractSlide):
    time_source: TimeSource
    christmas_date: datetime.datetime
    tree_points: List[Tuple[int, int]]

    def __init__(self, deps: Dependencies):
        self.time_source = deps.get_time_source()
        # Keep year and timezone, replace all other fields.
        self.christmas_date = self.time_source.now().replace(
            month=12, day=25, hour=0, minute=0, second=0, microsecond=0)

        # Preprocess the tree definition into a list of points
        self.tree_points = []
        for (j, row_def) in enumerate(_TREE_SHAPE):
            for i in range(row_def[0], row_def[0] + row_def[1]):
                self.tree_points.append((i, j))

    def is_enabled(self) -> bool:
        return self.christmas_date > self.time_source.now()

    def get_type(self) -> SlideType:
        return SlideType.HALF_WIDTH

    def draw(self, img: Image) -> None:
        draw = ImageDraw.Draw(img)
        self._draw_tree(draw, 8, 2)
        self._draw_countdown(draw, 44)

    def _draw_tree(self, draw: ImageDraw, x: int, y: int) -> None:
        # Star
        yellow = (255, 255, 0)
        draw.point((x+10, y-1), yellow)

        # Tree body
        dark_green = (0, 128, 0)
        for (j, row_def) in enumerate(_TREE_SHAPE):
            draw.line([(x+row_def[0], y+j), (x+row_def[0] +
                                             row_def[1]-1, y+j)], width=1, fill=dark_green)

        # Stump
        brown = (128, 64, 0)
        draw.rectangle([(x+9, y+25), (x+11, y+30)], fill=brown)

        # Lights
        colors = [AQUA, RED, GREEN, BLUE, YELLOW]
        for index, (i, j) in enumerate(_TREE_LIGHTS):
            c = colors[index % len(colors)]
            draw.point((x+i, y+j), c)

    def _draw_countdown(self, draw: ImageDraw, x: int) -> None:
        # Add one day to account for the fraction of today remaining.
        days = (self.christmas_date - self.time_source.now()).days + 1
        draw_string(draw, str(days), x, 8, Align.CENTER, GlyphSet.FONT_7PX, GREEN)
        draw_string(draw, "DAYS", x, 16, Align.CENTER, GlyphSet.FONT_7PX, RED)
