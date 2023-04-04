from abc import ABC, abstractmethod
from typing import Tuple

from PIL import ImageDraw  # type: ignore


class AbstractSlide(ABC):

    def is_enabled(self) -> bool:
        return True
    
    @abstractmethod
    def get_dimensions(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def draw(self, img: ImageDraw) -> None:
        pass