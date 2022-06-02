from re import L

from PIL import Image, ImageDraw

from constants import GRID_HEIGHT, GRID_WIDTH
from drawing import Color, PixelGrid

RENDER_SCALE = 10
DOT_PADDING = 2
MIN_BRIGHTNESS = 40


def write_grid_to_file(name: str, grid: PixelGrid):
    width = (GRID_WIDTH * RENDER_SCALE) + DOT_PADDING
    height = (GRID_HEIGHT * RENDER_SCALE) + DOT_PADDING
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    for j, row in enumerate(grid.pixels):
        for i, pixel in enumerate(row):
            x0 = (i * RENDER_SCALE) + DOT_PADDING
            x1 = x0 + RENDER_SCALE - (DOT_PADDING * 2)
            y0 = (j * RENDER_SCALE) + DOT_PADDING
            y1 = y0 + RENDER_SCALE - (DOT_PADDING * 2)
            draw.ellipse([x0, y0, x1, y1],
                         fill=_brightness_floor(pixel).to_tuple())
    img.save("render/" + name + ".png")


# Forces rendering a gray dot if no color is being displayed.
def _brightness_floor(c: Color) -> Color:
    def gt(a: int, b: int) -> int:
        if a > b:
            return a
        else:
            return b
    return Color(gt(c.r, MIN_BRIGHTNESS), gt(c.g, MIN_BRIGHTNESS), gt(c.b, MIN_BRIGHTNESS))
