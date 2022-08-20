import enum
import logging
from typing import List, Optional, Tuple

from PIL import Image  # type: ignore

from constants import GRID_HEIGHT, GRID_WIDTH
from glyphs import GLYPH_SET, Glyph


class Align(enum.Enum):
    LEFT = 1
    RIGHT = 2
    CENTER = 3


class Color:
    r: int
    g: int
    b: int

    def __init__(self, r: int = 0, g: int = 0, b: int = 0) -> None:
        self.r = r
        self.g = g
        self.b = b

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)


BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
AQUA = Color(0, 255, 255)
PURPLE = Color(255, 0, 255)
YELLOW = Color(255, 255, 0)


class PixelGrid:
    pixels: List[List[Color]]

    def __init__(self) -> None:
        self.pixels = [[Color() for x in range(0, GRID_WIDTH)]
                       for y in range(0, GRID_HEIGHT)]

    def set(self, x: int, y: int, c: Color) -> None:
        if x >= 0 and x < GRID_WIDTH and y >= 0 and y < GRID_HEIGHT:
            self.pixels[y][x] = c

    def draw_string(self, text: str, x: int, y: int, align: Align, c: Color, max_width: Optional[int] = None) -> None:
        # Collect the glpyhs that make up the input text string.
        # Stop retrieving them if we exceed the max draw size.
        text_as_glyphs: List[Glyph] = []
        text_glyph_width = 0
        for i in range(0, len(text)):
            if text[i] not in GLYPH_SET:
                logging.debug("Glyph %s not in global glyph set", text[i])
            glyph = GLYPH_SET[text[i]]
            text_glyph_width += glyph.width() + 1
            if max_width is not None and text_glyph_width > max_width:
                break
            text_as_glyphs.append(glyph)

        # Remove the kerning on the last letter
        text_glyph_width -= 1

        # Figure out where to start the letter drawing
        originX = 0
        if align == Align.LEFT:
            originX = x
        elif align == Align.RIGHT:
            originX = x - text_glyph_width + 1
        elif align == Align.CENTER:
            originX = x - int(text_glyph_width / 2)

        offsetX = 0
        for glyph in text_as_glyphs:
            self.draw_glyph(glyph, originX+offsetX, y, c)
            offsetX += glyph.width() + 1

    def draw_glyph_by_name(self, glyph_name: str, x: int, y: int, c: Color) -> None:
        if glyph_name not in GLYPH_SET:
            logging.debug("Glyph %s not in global glyph set", glyph_name)
            return
        return self.draw_glyph(GLYPH_SET[glyph_name], x, y, c)

    def draw_glyph(self, glyph: Glyph, x: int, y: int, c: Color) -> None:
        for j, row in enumerate(glyph.layout):
            for i, enabled in enumerate(row):
                if enabled:
                    self.set(x+i, y+j, c)

    def draw_error(self, title: str, message: str) -> None:
        self.draw_string(title, int(GRID_WIDTH/2), 8,
                         Align.CENTER, WHITE, GRID_WIDTH)
        self.draw_string(message, int(GRID_WIDTH/2), 16,
                         Align.CENTER, RED, GRID_WIDTH)

    def as_image(self) -> Image:
        img = Image.new('RGB', (GRID_WIDTH, GRID_HEIGHT))
        for j, row in enumerate(self.pixels):
            for i, pixel in enumerate(row):
                img.putpixel((i, j), pixel.to_tuple())
        return img
