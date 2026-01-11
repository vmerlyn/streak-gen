from pathlib import Path
import skia
from shapely.geometry import Polygon

def glyph_outline_svg_path(letter: str, font_path: Path, font_size: float):
    tf = skia.Typeface.MakeFromFile(str(font_path))
    font = skia.Font(tf, font_size)
    glyphs = font.textToGlyphs(letter)
    paths = font.getPaths(glyphs)
    glyph_path = paths[0]

    # Convert skia.Path to SVG path string
    path_commands = []
    for verb, points in glyph_path:
        if verb == skia.Path.kMove_Verb:
            path_commands.append(f"M {points[0].x()} {points[0].y()}")
        elif verb == skia.Path.kLine_Verb:
            path_commands.append(f"L {points[1].x()} {points[1].y()}")
        elif verb == skia.Path.kQuad_Verb:
            path_commands.append(f"Q {points[1].x()} {points[1].y()} {points[2].x()} {points[2].y()}")
        elif verb == skia.Path.kCubic_Verb:
            path_commands.append(f"C {points[1].x()} {points[1].y()} {points[2].x()} {points[2].y()} {points[3].x()} {points[3].y()}")
        elif verb == skia.Path.kConic_Verb:
            # Convert conic to cubic (simplified - could use ConvertConicToQuads for better accuracy)
            path_commands.append(f"Q {points[1].x()} {points[1].y()} {points[2].x()} {points[2].y()}")
        elif verb == skia.Path.kClose_Verb:
            path_commands.append("Z")

    svg_path_d = " ".join(path_commands)
    return svg_path_d, glyph_path

def skia_path_to_polygon(glyph_path: skia.Path, flatness: float = 1.0) -> Polygon:
    """Convert a Skia Path to a Shapely Polygon by flattening curves."""
    points = []
    current_pos = None

    for verb, pts in glyph_path:
        if verb == skia.Path.kMove_Verb:
            current_pos = (pts[0].x(), pts[0].y())
            if points:  # If we have previous points, this starts a new contour
                # For now, we'll just handle the outer boundary (first contour)
                pass
            else:
                points.append(current_pos)

        elif verb == skia.Path.kLine_Verb:
            current_pos = (pts[1].x(), pts[1].y())
            points.append(current_pos)

        elif verb == skia.Path.kQuad_Verb:
            # Flatten quadratic Bezier curve
            p0 = (pts[0].x(), pts[0].y())
            p1 = (pts[1].x(), pts[1].y())
            p2 = (pts[2].x(), pts[2].y())
            # Simple flattening: divide into segments
            num_segments = max(2, int(10 / flatness))
            for i in range(1, num_segments + 1):
                t = i / num_segments
                # Quadratic Bezier formula
                x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                points.append((x, y))
            current_pos = p2

        elif verb == skia.Path.kCubic_Verb:
            # Flatten cubic Bezier curve
            p0 = (pts[0].x(), pts[0].y())
            p1 = (pts[1].x(), pts[1].y())
            p2 = (pts[2].x(), pts[2].y())
            p3 = (pts[3].x(), pts[3].y())
            # Simple flattening: divide into segments
            num_segments = max(2, int(15 / flatness))
            for i in range(1, num_segments + 1):
                t = i / num_segments
                # Cubic Bezier formula
                x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
                y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
                points.append((x, y))
            current_pos = p3

        elif verb == skia.Path.kConic_Verb:
            # Flatten conic (treat similarly to quadratic for simplicity)
            p0 = (pts[0].x(), pts[0].y())
            p1 = (pts[1].x(), pts[1].y())
            p2 = (pts[2].x(), pts[2].y())
            num_segments = max(2, int(10 / flatness))
            for i in range(1, num_segments + 1):
                t = i / num_segments
                x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                points.append((x, y))
            current_pos = p2

        elif verb == skia.Path.kClose_Verb:
            # Close the contour (polygon will auto-close)
            pass

    # Create Shapely Polygon from points
    if len(points) < 3:
        raise ValueError(f"Not enough points to create a polygon: {len(points)}")

    return Polygon(points)
