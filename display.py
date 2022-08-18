from rgbmatrix import RGBMatrix, RGBMatrixOptions  # type: ignore

from drawing import PixelGrid


class Display:
    matrix: RGBMatrix

    def __init__(self) -> None:
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = 2
        options.pwm_bits = 11
        options.pwm_lsb_nanoseconds = 250
        options.brightness = 50
        options.show_refresh_rate = False
        options.hardware_mapping = 'adafruit-hat'
        self.matrix = RGBMatrix(options=options)

    def draw(self, grid: PixelGrid) -> None:
        self.matrix.SetImage(grid.as_image())

    def clear(self) -> None:
        self.matrix.Clear()
