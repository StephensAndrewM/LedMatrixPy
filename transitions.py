from abc import ABC, abstractmethod

from PIL import Image, ImageEnhance  # type: ignore


class Transition(ABC):

    @abstractmethod
    def merge(self, progress: float, img0: Image, img1: Image) -> Image:
        pass


class FadeToBlack(Transition):
    def merge(self, progress: float, img0: Image, img1: Image) -> Image:
        if progress < 0.5:
            enhancer = ImageEnhance.Brightness(img0)
            # 0 -> 1, 0.1 -> 0.8, 0.5 -> 0
            factor = 1-(progress*2)
            return enhancer.enhance(factor)
        else:
            # 0.5 -> 0, 0.9 -> 0.8, 1 -> 1
            factor = (progress-0.5)*2
            enhancer = ImageEnhance.Brightness(img1)
            return enhancer.enhance(factor)
