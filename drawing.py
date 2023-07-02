import enum
import logging
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw  # type: ignore

from abstractslide import SlideType
from constants import GRID_HEIGHT, GRID_WIDTH
from glyphs import GLYPH_SET, Glyph


class Align(enum.Enum):
    LEFT = 1
    RIGHT = 2
    CENTER = 3


Color = Tuple[int, int, int]


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
AQUA = (0, 255, 255)
PURPLE = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 220, 0)
GRAY = (128, 128, 128)


def create_slide(type: SlideType) -> Image:
    if type == SlideType.FULL_WIDTH:
        return Image.new("RGB", [GRID_WIDTH, GRID_HEIGHT])
    else:
        return Image.new("RGB", [int(GRID_WIDTH/2), GRID_HEIGHT])


def draw_string(img: ImageDraw, text: str, x: int, y: int, align: Align, c: Color, max_width: Optional[int] = None) -> None:
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
        draw_glyph(img, glyph, originX+offsetX, y, c)
        offsetX += glyph.width() + 1


def get_string_width(text: str) -> int:
    width = 0
    for i in range(0, len(text)):
        glyph = GLYPH_SET[text[i]]
        width += glyph.width() + 1
    return width-1


def draw_glyph_by_name(img: ImageDraw, glyph_name: str, x: int, y: int, c: Color) -> None:
    if glyph_name not in GLYPH_SET:
        logging.debug("Glyph %s not in global glyph set", glyph_name)
        return
    return draw_glyph(img, GLYPH_SET[glyph_name], x, y, c)


def draw_glyph(img: ImageDraw, glyph: Glyph, x: int, y: int, c: Color) -> None:
    for j, row in enumerate(glyph.layout):
        for i, enabled in enumerate(row):
            if enabled:
                img.point((x+i, y+j), c)


def draw_error(img: ImageDraw, title: str, message: str) -> None:
    draw_string(img, title, int(GRID_WIDTH/2), 8,
                Align.CENTER, WHITE, GRID_WIDTH)
    draw_string(img, message, int(GRID_WIDTH/2), 16,
                Align.CENTER, RED, GRID_WIDTH)
