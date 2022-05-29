from typing import List
from config import Config
from constants import GRID_HEIGHT, GRID_WIDTH


class Color:
    r: int
    g: int
    b: int

    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b


class PixelGrid:
    pixels: List[List[Color]]

    def __init__(self):
        self.pixels = [[Color() for x in range(0,GRID_WIDTH)] for y in range(0,GRID_HEIGHT)]

    def set(self, x:int, y:int, c:Color):
        self.pixels[y][x] = c