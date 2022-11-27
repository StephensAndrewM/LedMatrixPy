import datetime
import random
from typing import List, Optional, Tuple

from abstractslide import AbstractSlide
from deps import Dependencies
from drawing import (AQUA, BLUE, GREEN, ORANGE, RED, YELLOW, Align, Color,
                     PixelGrid)
from timesource import TimeSource

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
        self.christmas_date = datetime.datetime(
            self.time_source.now().year, 12, 25)

        # Preprocess the tree definition into a list of points
        self.tree_points = []
        for (j, row_def) in enumerate(_TREE_SHAPE):
            for i in range(row_def[0], row_def[0] + row_def[1]):
                self.tree_points.append((i, j))

    def is_enabled(self) -> bool:
        return self.christmas_date > self.time_source.now()

    def draw(self) -> PixelGrid:
        grid = PixelGrid()
        self._draw_tree(grid, 18, 2)
        self._draw_countdown(grid, 82)
        return grid

    def _draw_tree(self, grid: PixelGrid, x: int, y: int) -> None:
        # Star
        yellow = Color(255, 255, 0)
        grid.set(x+10, y-1, yellow)

        # Tree body
        dark_green = Color(0, 128, 0)
        for (i, j) in self.tree_points:
            grid.set(x+i, j+y, dark_green)

        # Stump
        brown = Color(255, 128, 0)
        grid.draw_box(x+9, y+25, 3, 5, brown)

        # Lights
        colors = [AQUA, RED, GREEN, BLUE, YELLOW]
        for index, (i, j) in enumerate(_TREE_LIGHTS):
            c = colors[index % len(colors)]
            grid.set(x+i, y+j, c)

    def _draw_countdown(self, grid: PixelGrid, x: int) -> None:
        days = (self.christmas_date - self.time_source.now()).days + 1
        box_width = grid.get_string_width(str(days)) + 8
        # Pad the box for shorter numbers
        if box_width < 19:
            box_width += 4
        grid.draw_empty_box(x-int(box_width/2), 1, box_width, 13, GREEN)

        grid.draw_string(str(days), x, 4, Align.CENTER, GREEN)

        grid.draw_string("DAYS UNTIL", x, 16, Align.CENTER, RED)
        grid.draw_string("CHRISTMAS", x, 24, Align.CENTER, RED)
