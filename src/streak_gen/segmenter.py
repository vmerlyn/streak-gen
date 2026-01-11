from pathlib import Path
import numpy as np
from shapely.geometry import Point
from .types import Region, Label, SegmentationResult
from .font_outline import glyph_outline_svg_path, skia_path_to_polygon
from .seeds import random_points_in_polygon
from .voronoi import voronoi_cells
import pyclipper

def segment_letter_to_regions(letter: str, font_path: Path, segments: int, font_size: float, inset: float):
    # Get letter outline and convert to polygon
    outline_d, glyph_path = glyph_outline_svg_path(letter, font_path, font_size)
    glyph_poly = skia_path_to_polygon(glyph_path)

    # Apply inset to the letter polygon (shrink it slightly)
    if inset > 0:
        # Use pyclipper to offset (inset) the polygon
        pco = pyclipper.PyclipperOffset()
        # Convert polygon to pyclipper format (list of points as tuples)
        path = [(x, y) for x, y in glyph_poly.exterior.coords[:-1]]
        pco.AddPath(path, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        # Negative offset = inset
        solution = pco.Execute(-inset)
        if solution:
            from shapely.geometry import Polygon
            inset_poly = Polygon(solution[0])
        else:
            inset_poly = glyph_poly
    else:
        inset_poly = glyph_poly

    # Generate random seed points within the inset polygon
    rng = np.random.default_rng(0)
    pts = random_points_in_polygon(inset_poly, segments, rng)

    # Compute Voronoi cells
    bbox = inset_poly.bounds  # (minx, miny, maxx, maxy)
    cells = voronoi_cells(pts, bbox)

    # Clip each Voronoi cell to the inset letter boundary
    regions = []
    labels = []
    for i in range(len(cells)):
        cell = cells[i]
        seed_pt = pts[i]

        # Clip cell to letter polygon
        clipped = cell.intersection(inset_poly)

        # Only keep valid polygons
        if clipped.is_valid and not clipped.is_empty and clipped.area > 0:
            regions.append(Region(id=i + 1, poly=clipped))
            # Place label at the seed point (simple and robust)
            labels.append(Label(id=i + 1, point=Point(seed_pt[0], seed_pt[1]), text=str(i + 1)))

    # Return the segmentation result
    return SegmentationResult(
        outline_path_svg=outline_d,
        segmentation_poly=inset_poly,
        regions=regions,
        labels=labels
    )
