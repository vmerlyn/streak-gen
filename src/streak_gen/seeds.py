import numpy as np
from shapely.geometry import Point, Polygon

def random_points_in_polygon(poly: Polygon, n: int, rng: np.random.Generator):
    minx, miny, maxx, maxy = poly.bounds
    pts = []
    while len(pts) < n:
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        if poly.contains(Point(x, y)):
            pts.append((x, y))
    return np.array(pts)
