import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union


def voronoi_cells(points, bbox):
    """
    Compute finite Voronoi cells from a set of points within a bounding box.

    Uses a simpler approach: add far-away mirror points around the bbox to force
    all interior regions to be finite, then clip to bbox.

    Args:
        points: Nx2 numpy array of seed points
        bbox: tuple (minx, miny, maxx, maxy) defining the bounding box

    Returns:
        list of Shapely Polygon objects representing Voronoi cells
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points for Voronoi diagram")

    # Create bounding box polygon
    minx, miny, maxx, maxy = bbox
    bbox_poly = box(minx, miny, maxx, maxy)

    # Calculate bbox dimensions
    width = maxx - minx
    height = maxy - miny

    # Add mirror/ghost points far outside the bbox to force all interior regions to be finite
    # Add points in a large grid around the bbox
    margin = max(width, height) * 5  # Far enough to ensure all regions are finite

    mirror_points = []
    # Add points around the perimeter at a distance
    for i in range(-2, 3):
        for j in range(-2, 3):
            if i == 0 and j == 0:
                continue  # Skip the center
            mx = minx + width/2 + i * margin
            my = miny + height/2 + j * margin
            mirror_points.append([mx, my])

    # Combine original points with mirror points
    all_points = np.vstack([points, mirror_points])

    # Compute Voronoi diagram with all points
    vor = Voronoi(all_points)

    cells = []

    # Extract cells only for the original points (not the mirror points)
    for point_idx in range(len(points)):
        region_idx = vor.point_region[point_idx]
        region = vor.regions[region_idx]

        # Skip empty or infinite regions (shouldn't happen with mirror points, but check anyway)
        if not region or -1 in region:
            # Fallback: use bbox
            cells.append(bbox_poly)
            continue

        # Get vertices of the Voronoi cell
        vertices = [vor.vertices[i] for i in region]

        # Create polygon from vertices
        if len(vertices) >= 3:
            cell_poly = Polygon(vertices)
            # Clip to bounding box
            clipped_cell = cell_poly.intersection(bbox_poly)
            cells.append(clipped_cell if clipped_cell.is_valid and not clipped_cell.is_empty else bbox_poly)
        else:
            cells.append(bbox_poly)

    return cells
