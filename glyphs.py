from collections import defaultdict
import os
from os import path
from typing import List, Dict
import pprint


class Glyph:
    char: str
    layout: List[List[bool]] = []

    def __init__(self, data: List[str]):
        if (len(data[0]) > 1):
            raise ValueError(
                'Char file contains invalid first line %s' % data[0])
        self.char = data[0]
        for j, line in enumerate(data[1:]):
            self.layout.append([])
            for i in range(0, len(line)):
                self.layout[j].append(self._charToBool(line[i]))

    def width(self) -> int:
        return len(self.layout[0])

    def _charToBool(self, char: str) -> bool:
        return char == 'X'


FALLBACK_GLYPH = Glyph([
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X"
])
glyph_set: Dict[str, Glyph] = defaultdict(lambda: FALLBACK_GLYPH)


def load_glyphs():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    glyph_dir = path.join(script_dir, "symbols/glyphs/")
    glyph_files = [f for f in os.listdir(
        glyph_dir) if path.isfile(path.join(glyph_dir, f))]
    for glyph_file in glyph_files:
        with open(path.join(glyph_dir, glyph_file)) as f:
            data = f.read().splitlines()
            glyph = Glyph(data)
            glyph_set[glyph.char] = glyph


load_glyphs()
print(glyph_set["A"])
print(glyph_set["B"])
