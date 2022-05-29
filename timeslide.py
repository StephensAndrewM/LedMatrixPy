from deps import Dependencies
from abstractslide import AbstractSlide
from drawing import Color, PixelGrid
from timesource import TimeSource

class TimeSlide(AbstractSlide):
    time_source:TimeSource

    def __init__(self, deps:Dependencies):
        self.time_source = deps.GetTimeSource()

    def draw(self) -> PixelGrid:
        grid = PixelGrid()
        white = Color(255,255,255)
        grid.set(0,0,white)
        return grid
