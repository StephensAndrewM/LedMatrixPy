from abc import ABC, abstractmethod

from PIL import ImageDraw  # type: ignore


class AbstractSlide(ABC):

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    def draw(self, img: ImageDraw) -> None:
        pass
