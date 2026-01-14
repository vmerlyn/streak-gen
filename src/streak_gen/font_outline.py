from pathlib import Path
import skia
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import translate

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
    """Convert a Skia Path to a Shapely Polygon by flattening curves.

    Handles multiple contours: first contour is exterior, subsequent ones are holes.
    """
    contours = []  # List of contours (each is a list of points)
    current_contour = []
    current_pos = None

    for verb, pts in glyph_path:
        if verb == skia.Path.kMove_Verb:
            # Starting a new contour
            if current_contour:
                # Save the previous contour
                contours.append(current_contour)
                current_contour = []

            current_pos = (pts[0].x(), pts[0].y())
            current_contour.append(current_pos)

        elif verb == skia.Path.kLine_Verb:
            current_pos = (pts[1].x(), pts[1].y())
            current_contour.append(current_pos)

        elif verb == skia.Path.kQuad_Verb:
            # Flatten quadratic Bezier curve
            p0 = (pts[0].x(), pts[0].y())
            p1 = (pts[1].x(), pts[1].y())
            p2 = (pts[2].x(), pts[2].y())
            num_segments = max(2, int(10 / flatness))
            for i in range(1, num_segments + 1):
                t = i / num_segments
                x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                current_contour.append((x, y))
            current_pos = p2

        elif verb == skia.Path.kCubic_Verb:
            # Flatten cubic Bezier curve
            p0 = (pts[0].x(), pts[0].y())
            p1 = (pts[1].x(), pts[1].y())
            p2 = (pts[2].x(), pts[2].y())
            p3 = (pts[3].x(), pts[3].y())
            num_segments = max(2, int(15 / flatness))
            for i in range(1, num_segments + 1):
                t = i / num_segments
                x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
                y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
                current_contour.append((x, y))
            current_pos = p3

        elif verb == skia.Path.kConic_Verb:
            # Flatten conic
            p0 = (pts[0].x(), pts[0].y())
            p1 = (pts[1].x(), pts[1].y())
            p2 = (pts[2].x(), pts[2].y())
            num_segments = max(2, int(10 / flatness))
            for i in range(1, num_segments + 1):
                t = i / num_segments
                x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                current_contour.append((x, y))
            current_pos = p2

        elif verb == skia.Path.kClose_Verb:
            # Close the current contour
            pass

    # Don't forget the last contour
    if current_contour:
        contours.append(current_contour)

    if len(contours) == 0:
        raise ValueError("No contours found in path")

    # First contour is the exterior, rest are holes
    exterior = contours[0]
    holes = contours[1:] if len(contours) > 1 else []

    if len(exterior) < 3:
        raise ValueError(f"Not enough points in exterior: {len(exterior)}")

    # Create Shapely Polygon with exterior and holes
    return Polygon(shell=exterior, holes=holes)


def word_outline_svg_path(word: str, font_path: Path, font_size: float):
    """Get the outline for an entire word with proper letter spacing.

    Returns:
        (svg_path_d, combined_polygon, letter_polygons): SVG path string, Shapely polygon for the word,
        and list of individual letter polygons
    """
    tf = skia.Typeface.MakeFromFile(str(font_path))
    font = skia.Font(tf, font_size)

    # Get glyphs and their positions
    glyphs = font.textToGlyphs(word)

    # Get widths for each glyph to position them
    widths = font.getWidths(glyphs)

    # Get paths for each glyph
    paths = font.getPaths(glyphs)

    # Process each letter
    svg_paths = []
    polygons = []
    x_offset = 0.0

    for i, (glyph_path, width) in enumerate(zip(paths, widths)):
        if glyph_path is None:
            # Space or missing glyph
            x_offset += width
            continue

        # Convert path to polygon
        poly = skia_path_to_polygon(glyph_path)

        # Clean up polygon geometry with buffer(0) to fix topology issues
        poly = poly.buffer(0)

        # Translate polygon to its position in the word
        if x_offset > 0:
            poly = translate(poly, xoff=x_offset)

        polygons.append(poly)

        # Convert to SVG path and translate
        path_commands = []
        for verb, points in glyph_path:
            if verb == skia.Path.kMove_Verb:
                path_commands.append(f"M {points[0].x() + x_offset} {points[0].y()}")
            elif verb == skia.Path.kLine_Verb:
                path_commands.append(f"L {points[1].x() + x_offset} {points[1].y()}")
            elif verb == skia.Path.kQuad_Verb:
                path_commands.append(f"Q {points[1].x() + x_offset} {points[1].y()} {points[2].x() + x_offset} {points[2].y()}")
            elif verb == skia.Path.kCubic_Verb:
                path_commands.append(f"C {points[1].x() + x_offset} {points[1].y()} {points[2].x() + x_offset} {points[2].y()} {points[3].x() + x_offset} {points[3].y()}")
            elif verb == skia.Path.kConic_Verb:
                path_commands.append(f"Q {points[1].x() + x_offset} {points[1].y()} {points[2].x() + x_offset} {points[2].y()}")
            elif verb == skia.Path.kClose_Verb:
                path_commands.append("Z")

        svg_paths.append(" ".join(path_commands))

        # Move to next letter position
        x_offset += width

    # Combine all polygons into one
    if len(polygons) == 0:
        raise ValueError(f"No valid glyphs found in word: {word}")
    elif len(polygons) == 1:
        combined_poly = polygons[0]
    else:
        combined_poly = unary_union(polygons)

    # Combine all SVG paths
    svg_path_d = " ".join(svg_paths)

    return svg_path_d, combined_poly, polygons
