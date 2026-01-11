import svgwrite
from .types import Region, Label

def polygon_to_svg_path(poly):
    """Convert a Shapely Polygon to an SVG path string."""
    coords = list(poly.exterior.coords)
    if not coords:
        return ""

    path_parts = [f"M {coords[0][0]} {coords[0][1]}"]
    for x, y in coords[1:]:
        path_parts.append(f"L {x} {y}")
    path_parts.append("Z")

    return " ".join(path_parts)


def render_letter_svg(page, margin, outline_path_svg, regions, labels):
    # Page dimensions (US Letter size in points)
    w, h = (612, 792)

    # Calculate bounding box from all regions
    if not regions:
        # Fallback if no regions
        min_x, min_y, max_x, max_y = 0, 0, w, h
    else:
        all_bounds = [r.poly.bounds for r in regions]
        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)

    # Calculate dimensions
    glyph_width = max_x - min_x
    glyph_height = max_y - min_y

    # Available space on page (accounting for margins)
    available_width = w - 2 * margin
    available_height = h - 2 * margin

    # Calculate scale to fit letter on page
    scale_x = available_width / glyph_width if glyph_width > 0 else 1
    scale_y = available_height / glyph_height if glyph_height > 0 else 1
    scale = min(scale_x, scale_y)  # Uniform scaling

    # Calculate translation to center the letter
    # Coordinates are already in SVG space (Y-down) from font_outline conversion
    scaled_width = glyph_width * scale
    scaled_height = glyph_height * scale
    translate_x = margin + (available_width - scaled_width) / 2 - min_x * scale
    translate_y = margin + (available_height - scaled_height) / 2 - min_y * scale

    # Create SVG
    dwg = svgwrite.Drawing(size=(w, h))
    dwg.add(dwg.rect(insert=(0, 0), size=(w, h), fill="white"))

    # Create a group with transformation
    transform = f"translate({translate_x}, {translate_y}) scale({scale}, {scale})"
    g = dwg.g(transform=transform)
    dwg.add(g)

    # Render each region boundary without fill, just showing the divisions
    for r in regions:
        path_d = polygon_to_svg_path(r.poly)
        # Show region boundaries with thin strokes, no fill
        g.add(dwg.path(d=path_d, fill="none", stroke="gray", stroke_width=1/scale))

    # Add the letter outline on top
    g.add(dwg.path(d=outline_path_svg, fill="none", stroke="black", stroke_width=4/scale))

    # Add labels
    for lab in labels:
        g.add(dwg.text(lab.text, insert=(lab.point.x, lab.point.y),
                      font_size=f"{12/scale}px",
                      text_anchor="middle",
                      dominant_baseline="middle"))

    return dwg.tostring()
