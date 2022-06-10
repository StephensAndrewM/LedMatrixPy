from collections import defaultdict
from os import listdir, path
from typing import Dict, List

_SPACE_WIDTH = 4


class Glyph:
    char: str
    layout: List[List[bool]]

    def __init__(self, data: List[str]):
        if (len(data[0]) > 1):
            raise ValueError(
                'Char file contains invalid first line %s' % data[0])
        self.char = data[0]

        self.layout = []
        for j, line in enumerate(data[1:]):
            self.layout.append([self._charToBool(c) for c in line])

    def width(self) -> int:
        return len(self.layout[0])

    def height(self) -> int:
        return len(self.layout)

    def __str__(self) -> str:
        return "[%s] (%d x %d)" % (self.char, self.width(), self.height())

    def __repr__(self) -> str:
        return "[%s] (%d x %d)" % (self.char, self.width(), self.height())

    def _charToBool(self, char: str) -> bool:
        return char == 'X'


FALLBACK_GLYPH = Glyph([
    "�",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X"
])
GLYPH_SET: Dict[str, Glyph] = defaultdict(lambda: FALLBACK_GLYPH)

SPACE_GLYPH = Glyph([
    " ",
    "." * _SPACE_WIDTH
])
GLYPH_SET[" "] = SPACE_GLYPH


def load_glyphs() -> None:
    script_dir = path.dirname(path.realpath(__file__))
    glyph_dir = path.join(script_dir, "symbols/glyphs/")
    glyph_files = [f for f in listdir(
        glyph_dir) if path.isfile(path.join(glyph_dir, f))]
    for glyph_file in glyph_files:
        with open(path.join(glyph_dir, glyph_file)) as f:
            data = f.read().splitlines()
            glyph = Glyph(data)
            GLYPH_SET[glyph.char] = glyph


load_glyphs()
