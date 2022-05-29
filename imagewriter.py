from re import L
from PIL import Image, ImageDraw
import os, sys
from constants import GRID_HEIGHT, GRID_WIDTH
from drawing import PixelGrid

RENDER_SCALE = 8
DOT_PADDING = 1

def write_grid_to_file(name:str, grid:PixelGrid):
    img = Image.new('RGB', (GRID_WIDTH * RENDER_SCALE, GRID_HEIGHT * RENDER_SCALE))
    draw = ImageDraw.Draw(img)
    for j,row in enumerate(grid.pixels):
        for i,pixel in enumerate(row):
            x0 = (i * RENDER_SCALE) + DOT_PADDING
            x1 = (i * RENDER_SCALE) + RENDER_SCALE - (DOT_PADDING*2)
            y0 = (j * RENDER_SCALE) + DOT_PADDING
            y1 = (j * RENDER_SCALE) + RENDER_SCALE - (DOT_PADDING*2)
            draw.ellipse([x0, y0, x1, y1])

    img.save(name + ".png")