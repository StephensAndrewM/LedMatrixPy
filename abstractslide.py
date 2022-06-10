from abc import ABC, abstractmethod

from drawing import PixelGrid


class AbstractSlide(ABC):

    def initialize(self) -> None:
        pass

    def terminate(self) -> None:
        pass

    def is_enabled(self) -> bool:
        return True

    def start_draw(self) -> None:
        pass

    def stop_draw(self) -> None:
        pass

    @abstractmethod
    def draw(self) -> PixelGrid:
        pass
