from dataclasses import dataclass
from shapely.geometry import Polygon, Point, LineString

@dataclass(frozen=True)
class Region:
    id: int
    poly: Polygon

@dataclass(frozen=True)
class Label:
    id: int
    point: Point
    text: str

@dataclass(frozen=True)
class SegmentationResult:
    outline_path_svg: str
    segmentation_poly: Polygon
    regions: list[Region]
    labels: list[Label]
    voronoi_edges: list[LineString] = None  # Optional Voronoi cell boundaries
