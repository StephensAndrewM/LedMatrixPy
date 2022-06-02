from abc import ABC, abstractmethod

from drawing import PixelGrid


class AbstractSlide(ABC):

    def initialize(self):
        pass

    def terminate(self):
        pass

    def is_enabled(self) -> bool:
        return True

    def start_draw(self):
        pass

    def stop_draw(self):
        pass

    @abstractmethod
    def draw(self) -> PixelGrid:
        pass
