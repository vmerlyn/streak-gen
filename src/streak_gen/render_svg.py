import svgwrite
from .types import Region, Label

def polygon_to_svg_path(geom):
    """Convert a Shapely Polygon or MultiPolygon to an SVG path string."""

    def single_polygon_to_path(poly):
        """Convert a single polygon (with potential holes) to SVG path."""
        path_parts = []

        # Exterior ring
        coords = list(poly.exterior.coords)
        if coords:
            path_parts.append(f"M {coords[0][0]} {coords[0][1]}")
            for x, y in coords[1:]:
                path_parts.append(f"L {x} {y}")
            path_parts.append("Z")

        # Interior rings (holes) - these create cutouts
        for interior in poly.interiors:
            coords = list(interior.coords)
            if coords:
                path_parts.append(f"M {coords[0][0]} {coords[0][1]}")
                for x, y in coords[1:]:
                    path_parts.append(f"L {x} {y}")
                path_parts.append("Z")

        return " ".join(path_parts)

    # Handle MultiPolygon
    if geom.geom_type == 'MultiPolygon':
        paths = []
        for poly in geom.geoms:
            paths.append(single_polygon_to_path(poly))
        return " ".join(paths)

    # Handle single Polygon
    return single_polygon_to_path(geom)


def render_letter_svg(page, margin, outline_path_svg, regions, labels, voronoi_edges=None):
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

    # Render each region boundary (only exterior, not interior holes)
    for r in regions:
        # Handle both Polygon and MultiPolygon
        if r.poly.geom_type == 'MultiPolygon':
            # For MultiPolygon, render exterior of each polygon
            for poly in r.poly.geoms:
                coords = list(poly.exterior.coords)
                if coords:
                    path_parts = [f"M {coords[0][0]} {coords[0][1]}"]
                    for x, y in coords[1:]:
                        path_parts.append(f"L {x} {y}")
                    path_parts.append("Z")
                    path_d = " ".join(path_parts)
                    g.add(dwg.path(d=path_d, fill="none", stroke="gray", stroke_width=1/scale))
        else:
            # Single Polygon - only render exterior ring, not holes
            coords = list(r.poly.exterior.coords)
            if coords:
                path_parts = [f"M {coords[0][0]} {coords[0][1]}"]
                for x, y in coords[1:]:
                    path_parts.append(f"L {x} {y}")
                path_parts.append("Z")
                path_d = " ".join(path_parts)
                g.add(dwg.path(d=path_d, fill="none", stroke="gray", stroke_width=1/scale))

    # Add the letter outline on top
    g.add(dwg.path(d=outline_path_svg, fill="none", stroke="black", stroke_width=4/scale))

    # Add labels LAST with white background so they're always visible
    for lab in labels:
        # Add white background rectangle for visibility
        text_width = len(lab.text) * 8  # Approximate width
        text_height = 14
        g.add(dwg.rect(
            insert=(lab.point.x - text_width/2, lab.point.y - text_height/2),
            size=(text_width, text_height),
            fill="white",
            opacity=0.8
        ))

        # Add label text on top of background
        g.add(dwg.text(lab.text, insert=(lab.point.x, lab.point.y),
                      font_size="14px",
                      text_anchor="middle",
                      dominant_baseline="middle",
                      fill="black",
                      font_weight="bold"))

    return dwg.tostring()
