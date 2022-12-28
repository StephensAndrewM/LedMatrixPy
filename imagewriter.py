from PIL import Image, ImageDraw  # type: ignore

from constants import GRID_HEIGHT, GRID_WIDTH
from drawing import Color

RENDER_SCALE = 10
DOT_PADDING = 2
MIN_BRIGHTNESS = 40


def write_grid_to_file(name: str, base_img: Image) -> None:
    width = (GRID_WIDTH * RENDER_SCALE) + DOT_PADDING
    height = (GRID_HEIGHT * RENDER_SCALE) + DOT_PADDING
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    for j in range(0, GRID_HEIGHT):
        for i in range(0, GRID_WIDTH):
            pixel = base_img.getpixel((i, j))
            x0 = (i * RENDER_SCALE) + DOT_PADDING
            x1 = x0 + RENDER_SCALE - (DOT_PADDING * 2)
            y0 = (j * RENDER_SCALE) + DOT_PADDING
            y1 = y0 + RENDER_SCALE - (DOT_PADDING * 2)
            draw.ellipse([x0, y0, x1, y1],
                         fill=_brightness_floor(pixel))
    img.save("render/" + name + ".png")


# Forces rendering a gray dot if no color is being displayed.
def _brightness_floor(c: Color) -> Color:
    def gt(a: int, b: int) -> int:
        if a > b:
            return a
        else:
            return b
    return (gt(c[0], MIN_BRIGHTNESS), gt(c[1], MIN_BRIGHTNESS), gt(c[2], MIN_BRIGHTNESS))
