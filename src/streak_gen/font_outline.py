from pathlib import Path
import skia
from shapely.geometry import Polygon

def glyph_outline_svg_path(letter: str, font_path: Path, font_size: float):
    tf = skia.Typeface.MakeFromFile(str(font_path))
    font = skia.Font(tf, font_size)
    glyphs = font.textToGlyphs(letter)
    paths = font.getPaths(glyphs)
    glyph_path = paths[0]
    return glyph_path.toSVGString(), glyph_path

def skia_path_to_polygon(glyph_path: skia.Path, flatness: float = 1.0) -> Polygon:
    raise NotImplementedError("Implement Skia path → Shapely polygon conversion.")
