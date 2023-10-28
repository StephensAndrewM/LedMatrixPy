import enum
import re
from collections import defaultdict
from os import listdir, path
from typing import Dict, List, Tuple
import logging
_SPACE_WIDTH = 3


class GlyphSet(enum.Enum):
    FONT_7PX = 1
    WEATHER = 2


_ALL_GLYPHS_TO_DIRECTORY = {
    GlyphSet.FONT_7PX: 'symbols/glyphs_7px',
    GlyphSet.WEATHER: 'symbols/weather_onebit',
}


class Glyph:
    name: str
    layout: List[List[bool]]

    def __init__(self, name: str, data: List[str]):
        self.name = name
        self.layout = []
        for line in data:
            self.layout.append([self._charToBool(c) for c in line])

    def width(self) -> int:
        return len(self.layout[0])

    def height(self) -> int:
        return len(self.layout)

    def __str__(self) -> str:
        return "[%s] (%d x %d)" % (self.name, self.width(), self.height())

    def __repr__(self) -> str:
        return "[%s] (%d x %d)" % (self.name, self.width(), self.height())

    # Interprets X as true, anything else as false.
    def _charToBool(self, char: str) -> bool:
        return char == 'X'


FALLBACK_GLYPH = Glyph("�", [
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X",
    "X.X.X.",
    ".X.X.X"
])
ALL_GLYPHS: Dict[Tuple[GlyphSet, str],
                Glyph] = defaultdict(lambda: FALLBACK_GLYPH)

# A space doesn't follow the file format well so add it here manually, in sets where it's relevant.
SPACE_GLYPH = Glyph(" ", [
    "." * _SPACE_WIDTH
])
ALL_GLYPHS[GlyphSet.FONT_7PX, " "] = SPACE_GLYPH


def _store_glyph(set: GlyphSet, name: str, data:List[str]) -> None:
    # In case of two blank lines in a row, don't store anything.
    if name and len(data) > 0:
        # Don't accidentally read a data line as a glyph name.
        if re.match("[\.X]{2,}", name):
            logging.warning("Suspicious glyph name: %s" % name)
        glyph = Glyph(name, data)
        ALL_GLYPHS[set, name] = glyph

def _process_glyph_file(set: GlyphSet, filename: str) -> None:
    found_name: str = ""
    found_data: List[str] = []
    with open(filename) as f:
        data = f.read().splitlines()
        for line in data:
            # If empty string, we finished reading a char.
            if not line:
                _store_glyph(set, found_name, found_data)
                found_name = ""
                found_data = []

            # We got the glyph name, now we need to read its data.
            elif found_name:
                found_data.append(line)

            # If we don't have a name yet, the first line specifies it.
            else:
                found_name = line
        
        # Store anything remaining at end of parsing file.
        _store_glyph(set, found_name, found_data)


def _load_glyphs() -> None:
    script_dir = path.dirname(path.realpath(__file__))
    for set, glyph_subdir in _ALL_GLYPHS_TO_DIRECTORY.items():
        full_glyph_dir = path.join(script_dir, glyph_subdir)
        for f in listdir(full_glyph_dir):
            full_filename = path.join(full_glyph_dir, f)
            # Don't try to read things that aren't real files, or aren't .txt files
            if path.isfile(full_filename) and re.match(".*\.txt", f):
                _process_glyph_file(set, full_filename)


# Run on startup outside of the main event flow.
_load_glyphs()
