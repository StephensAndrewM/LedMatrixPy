from abc import ABC, abstractmethod
from enum import Enum

from PIL import Image  # type: ignore


class SlideType(Enum):
    FULL_WIDTH = 1
    HALF_WIDTH = 2


class AbstractSlide(ABC):

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    def get_type(self) -> SlideType:
        pass

    @abstractmethod
    def draw(self, img: Image) -> None:
        pass
