from abc import ABC, abstractmethod

from drawing import PixelGrid

from constants import GRID_HEIGHT, GRID_WIDTH


class Transition(ABC):

    @abstractmethod
    def merge(self, progress: float, g0: PixelGrid, g1: PixelGrid) -> PixelGrid:
        pass


class FadeToBlack(Transition):
    def merge(self, progress: float, g0: PixelGrid, g1: PixelGrid) -> PixelGrid:
        if progress < 0.5:
            target_image = g0
            darken_amount = progress*2
        else:
            darken_amount = (1-progress)*2
            target_image = g1

        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                target_image.darken(i, j, darken_amount)

        return target_image
