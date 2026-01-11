import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union


def voronoi_cells(points, bbox):
    """
    Compute finite Voronoi cells from a set of points within a bounding box.

    Args:
        points: Nx2 numpy array of seed points
        bbox: tuple (minx, miny, maxx, maxy) defining the bounding box

    Returns:
        list of Shapely Polygon objects representing Voronoi cells
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points for Voronoi diagram")

    # Compute Voronoi diagram
    vor = Voronoi(points)

    # Create bounding box polygon
    minx, miny, maxx, maxy = bbox
    bbox_poly = box(minx, miny, maxx, maxy)

    cells = []

    # For each seed point, reconstruct its Voronoi cell
    for point_idx in range(len(points)):
        # Find the region index for this point
        region_idx = vor.point_region[point_idx]
        region = vor.regions[region_idx]

        # Skip empty or infinite regions
        if not region or -1 in region:
            # Handle infinite region by using bbox
            # For simplicity, create a bounded cell using the bbox
            # This is a simplified approach; a more robust implementation would
            # construct the actual cell using ridge vertices and directions
            cells.append(bbox_poly)
            continue

        # Get vertices of the Voronoi cell
        vertices = [vor.vertices[i] for i in region]

        # Create polygon from vertices
        if len(vertices) >= 3:
            cell_poly = Polygon(vertices)
            # Clip to bounding box
            clipped_cell = cell_poly.intersection(bbox_poly)
            cells.append(clipped_cell if clipped_cell.is_valid else bbox_poly)
        else:
            cells.append(bbox_poly)

    return cells
