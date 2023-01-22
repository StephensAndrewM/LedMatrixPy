from abc import ABC, abstractmethod

from PIL import Image  # type: ignore
from rgbmatrix import RGBMatrix, RGBMatrixOptions  # type: ignore


class Display():
    def draw(self, img: Image) -> None:
        pass

    def clear(self) -> None:
        pass


class MatrixDisplay(Display):
    matrix: RGBMatrix

    def __init__(self) -> None:
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = 2
        options.pwm_bits = 11
        options.brightness = 40
        options.show_refresh_rate = False
        options.limit_refresh_rate_hz = 120
        # Sudo is needed to call ntpdate
        options.drop_privileges = False
        options.hardware_mapping = 'adafruit-hat-pwm'
        self.matrix = RGBMatrix(options=options)

    def draw(self, img: Image) -> None:
        self.matrix.SetImage(img)

    def clear(self) -> None:
        self.matrix.Clear()
