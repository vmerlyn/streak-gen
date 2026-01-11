from pathlib import Path
import numpy as np
from .types import Region, Label, SegmentationResult
from .font_outline import glyph_outline_svg_path, skia_path_to_polygon
from .seeds import random_points_in_polygon

def segment_letter_to_regions(letter: str, font_path: Path, segments: int, font_size: float, inset: float):
    outline_d, glyph_path = glyph_outline_svg_path(letter, font_path, font_size)
    glyph_poly = skia_path_to_polygon(glyph_path)
    rng = np.random.default_rng(0)
    pts = random_points_in_polygon(glyph_poly, segments, rng)
    raise NotImplementedError("Voronoi + clipping + exact-N enforcement not implemented.")
