from abc import ABC, abstractmethod

from drawing import PixelGrid


class AbstractSlide(ABC):

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    def draw(self) -> PixelGrid:
        pass
