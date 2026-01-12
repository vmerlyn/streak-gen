from pathlib import Path
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from .types import Region, Label, SegmentationResult
from .font_outline import glyph_outline_svg_path, skia_path_to_polygon, word_outline_svg_path
from .seeds import random_points_in_polygon
from .voronoi import voronoi_cells
import pyclipper
from scipy.spatial import Voronoi

def segment_letter_to_regions(letter: str, font_path: Path, segments: int, font_size: float, inset: float):
    # Get letter outline and convert to polygon
    outline_d, glyph_path = glyph_outline_svg_path(letter, font_path, font_size)
    glyph_poly = skia_path_to_polygon(glyph_path)

    # Apply inset to the letter polygon (shrink it slightly)
    # The buffer operation with negative value will automatically handle both:
    # - Shrinking the exterior boundary
    # - Expanding the holes (interior rings)
    if inset > 0:
        # Negative buffer shrinks exterior and expands holes
        inset_poly = glyph_poly.buffer(-inset)

        # Clean up geometry
        if not inset_poly.is_valid or inset_poly.is_empty:
            inset_poly = glyph_poly.buffer(-inset * 0.5)  # Try with less aggressive inset
    else:
        inset_poly = glyph_poly

    # Generate random seed points within the inset polygon
    rng = np.random.default_rng(0)
    pts = random_points_in_polygon(inset_poly, segments, rng)

    # Apply Lloyd's relaxation to improve spatial distribution
    # This moves seeds toward the centroid of their Voronoi cells
    for iteration in range(3):  # 3 iterations usually enough
        bbox = inset_poly.bounds
        cells = voronoi_cells(pts, bbox)

        new_pts = []
        for i, cell in enumerate(cells):
            # Clip cell to polygon
            clipped = cell.intersection(inset_poly)

            if clipped.is_valid and not clipped.is_empty and clipped.area > 0:
                # Move seed to centroid of clipped cell
                centroid = clipped.centroid
                # Check if centroid is inside the polygon
                if inset_poly.contains(centroid):
                    new_pts.append([centroid.x, centroid.y])
                else:
                    # If centroid is outside (due to complex shape), keep original
                    new_pts.append(pts[i])
            else:
                # Keep original point if cell becomes invalid
                new_pts.append(pts[i])

        pts = np.array(new_pts)

    # Compute final Voronoi cells with relaxed points
    bbox = inset_poly.bounds  # (minx, miny, maxx, maxy)
    cells = voronoi_cells(pts, bbox)

    # Also compute Voronoi diagram to extract edges
    vor = Voronoi(pts)

    # Extract Voronoi edges that lie within the polygon
    voronoi_edges = []
    for ridge_vertices in vor.ridge_vertices:
        if -1 not in ridge_vertices:  # Skip infinite ridges
            p1 = vor.vertices[ridge_vertices[0]]
            p2 = vor.vertices[ridge_vertices[1]]
            edge = LineString([(p1[0], p1[1]), (p2[0], p2[1])])

            # Clip edge to the inset polygon
            clipped_edge = edge.intersection(inset_poly)
            if not clipped_edge.is_empty and clipped_edge.geom_type == 'LineString':
                voronoi_edges.append(clipped_edge)

    # Clip each Voronoi cell to the inset letter boundary
    temp_regions = []
    for i in range(len(cells)):
        cell = cells[i]
        seed_pt = pts[i]

        # Clip cell to letter polygon
        clipped = cell.intersection(inset_poly)

        # Only keep valid polygons
        if clipped.is_valid and not clipped.is_empty and clipped.area > 0:
            # Store region with its centroid for sorting
            centroid = clipped.centroid
            temp_regions.append({
                'poly': clipped,
                'seed_pt': seed_pt,
                'centroid': centroid
            })

    # Sort regions spatially: top-to-bottom, then left-to-right
    # In SVG coordinates, y is negative at top, so sort by y ascending (most negative first)
    temp_regions.sort(key=lambda r: (r['centroid'].y, r['centroid'].x))

    # Now assign IDs based on sorted order
    regions = []
    labels = []
    for i, region_data in enumerate(temp_regions):
        clipped = region_data['poly']
        seed_pt = region_data['seed_pt']

        regions.append(Region(id=i + 1, poly=clipped))

        # Place label at representative point inside the clipped region
        # Use the seed point if it's inside, otherwise use representative_point
        label_pt = Point(seed_pt[0], seed_pt[1])
        if not clipped.contains(label_pt):
            label_pt = clipped.representative_point()
        labels.append(Label(id=i + 1, point=label_pt, text=str(i + 1)))

    # Return the segmentation result
    return SegmentationResult(
        outline_path_svg=outline_d,
        segmentation_poly=inset_poly,
        regions=regions,
        labels=labels,
        voronoi_edges=voronoi_edges
    )


def segment_word_to_regions(word: str, font_path: Path, segments: int, font_size: float, inset: float):
    """Segment a word into N regions using Voronoi tessellation.

    Args:
        word: The word to segment
        font_path: Path to the font file
        segments: Number of regions to create
        font_size: Font size in points
        inset: Amount to inset the boundary

    Returns:
        SegmentationResult with regions distributed across the entire word
    """
    # Get word outline
    outline_d, word_poly = word_outline_svg_path(word, font_path, font_size)

    # Apply inset to the word polygon (shrink it slightly)
    if inset > 0:
        # Use pyclipper to offset (inset) the polygon
        pco = pyclipper.PyclipperOffset()

        # Handle MultiPolygon (word with separate letters like 'i' with dot)
        if word_poly.geom_type == 'MultiPolygon':
            inset_polys = []
            for poly in word_poly.geoms:
                path = [(x, y) for x, y in poly.exterior.coords[:-1]]
                pco.Clear()
                pco.AddPath(path, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
                solution = pco.Execute(-inset)
                if solution:
                    inset_polys.append(Polygon(solution[0]))
            if inset_polys:
                from shapely.ops import unary_union
                inset_poly = unary_union(inset_polys)
            else:
                inset_poly = word_poly
        else:
            # Single polygon
            path = [(x, y) for x, y in word_poly.exterior.coords[:-1]]
            pco.AddPath(path, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            solution = pco.Execute(-inset)
            if solution:
                inset_poly = Polygon(solution[0])
            else:
                inset_poly = word_poly
    else:
        inset_poly = word_poly

    # Generate random seed points within the inset polygon
    rng = np.random.default_rng(0)
    pts = random_points_in_polygon(inset_poly, segments, rng)

    # Apply Lloyd's relaxation to improve spatial distribution
    for iteration in range(3):
        bbox = inset_poly.bounds
        cells = voronoi_cells(pts, bbox)

        new_pts = []
        for i, cell in enumerate(cells):
            clipped = cell.intersection(inset_poly)

            if clipped.is_valid and not clipped.is_empty and clipped.area > 0:
                centroid = clipped.centroid
                if inset_poly.contains(centroid):
                    new_pts.append([centroid.x, centroid.y])
                else:
                    new_pts.append(pts[i])
            else:
                new_pts.append(pts[i])

        pts = np.array(new_pts)

    # Compute final Voronoi cells with relaxed points
    bbox = inset_poly.bounds  # (minx, miny, maxx, maxy)
    cells = voronoi_cells(pts, bbox)

    # Also compute Voronoi diagram to extract edges
    vor = Voronoi(pts)

    # Extract Voronoi edges that lie within the polygon
    voronoi_edges = []
    for ridge_vertices in vor.ridge_vertices:
        if -1 not in ridge_vertices:  # Skip infinite ridges
            p1 = vor.vertices[ridge_vertices[0]]
            p2 = vor.vertices[ridge_vertices[1]]
            edge = LineString([(p1[0], p1[1]), (p2[0], p2[1])])

            # Clip edge to the inset polygon
            clipped_edge = edge.intersection(inset_poly)
            if not clipped_edge.is_empty and clipped_edge.geom_type == 'LineString':
                voronoi_edges.append(clipped_edge)

    # Clip each Voronoi cell to the inset word boundary
    temp_regions = []
    for i in range(len(cells)):
        cell = cells[i]
        seed_pt = pts[i]

        # Clip cell to word polygon
        clipped = cell.intersection(inset_poly)

        # Only keep valid polygons
        if clipped.is_valid and not clipped.is_empty and clipped.area > 0:
            # Store region with its centroid for sorting
            centroid = clipped.centroid
            temp_regions.append({
                'poly': clipped,
                'seed_pt': seed_pt,
                'centroid': centroid
            })

    # Sort regions spatially: top-to-bottom, then left-to-right
    # In SVG coordinates, y is negative at top, so sort by y ascending (most negative first)
    temp_regions.sort(key=lambda r: (r['centroid'].y, r['centroid'].x))

    # Now assign IDs based on sorted order
    regions = []
    labels = []
    for i, region_data in enumerate(temp_regions):
        clipped = region_data['poly']
        seed_pt = region_data['seed_pt']

        regions.append(Region(id=i + 1, poly=clipped))

        # Place label at representative point inside the clipped region
        label_pt = Point(seed_pt[0], seed_pt[1])
        if not clipped.contains(label_pt):
            label_pt = clipped.representative_point()
        labels.append(Label(id=i + 1, point=label_pt, text=str(i + 1)))

    # Return the segmentation result
    return SegmentationResult(
        outline_path_svg=outline_d,
        segmentation_poly=inset_poly,
        regions=regions,
        labels=labels,
        voronoi_edges=voronoi_edges
    )
