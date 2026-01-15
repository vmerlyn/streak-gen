"""Layout all 12 months on a single letter-sized page."""
from pathlib import Path
from .segmenter import segment_word_to_regions
import svgwrite

# Month data: (name, days, suggested_rotation)
MONTHS = [
    ("JANUARY", 31, 0),
    ("FEBRUARY", 28, 0),
    ("MARCH", 31, 90),
    ("APRIL", 30, 90),
    ("MAY", 31, 90),
    ("JUNE", 30, 0),
    ("JULY", 31, 90),
    ("AUGUST", 31, 0),
    ("SEPTEMBER", 30, 0),
    ("OCTOBER", 31, 0),
    ("NOVEMBER", 30, 90),
    ("DECEMBER", 31, 0),
]

def layout_year(font_path: Path, out_path: Path):
    """Generate all 12 months laid out on a letter-sized page in landscape."""

    # Letter size in landscape (11" x 8.5")
    page_width = 792
    page_height = 612
    margin = 20

    # Generate segmentation for all months
    print("Generating month segmentations...")
    month_data = []
    for month_name, days, rotation in MONTHS:
        print(f"  {month_name} ({days} days)...")
        result = segment_word_to_regions(
            month_name,
            font_path,
            days,
            font_size=800.0,  # Doubled again from 400.0
            inset=4.0
        )

        # Calculate bounds
        all_bounds = [r.poly.bounds for r in result.regions]
        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)

        width = max_x - min_x
        height = max_y - min_y

        month_data.append({
            'name': month_name,
            'days': days,
            'result': result,
            'bounds': (min_x, min_y, max_x, max_y),
            'width': width,
            'height': height,
            'rotation': rotation
        })

    # Calculate layout positions - left to right with wrapping
    scale = 0.08  # Reduced to fit doubled font size
    available_width = page_width - 2 * margin

    # Calculate scaled widths for each month
    scaled_widths = []
    scaled_heights = []
    for month in month_data:
        scaled_widths.append(month['width'] * scale)
        scaled_heights.append(month['height'] * scale)

    # Place months left to right with wrapping
    layout = []
    current_x = margin
    current_y = margin
    row_height = 0
    gap = 20  # Increased gap between months

    for i, (width, height) in enumerate(zip(scaled_widths, scaled_heights)):
        # Check if month fits on current line
        if current_x + width > page_width - margin and current_x > margin:
            # Move to next line
            current_x = margin
            current_y += row_height + gap
            row_height = 0

        # Place month at current position
        layout.append((current_x, current_y, scale, 0))

        # Update position for next month
        current_x += width + gap
        row_height = max(row_height, height)

    # Create SVG
    print("Creating layout...")
    dwg = svgwrite.Drawing(size=(page_width, page_height))
    dwg.add(dwg.rect(insert=(0, 0), size=(page_width, page_height), fill="white"))

    # Render each month
    for i, month in enumerate(month_data):
        x, y, scale, rotation = layout[i]

        # Create group for this month with transform
        if rotation == 0:
            transform = f"translate({x}, {y}) scale({scale})"
        else:
            # Rotate around the placement point
            transform = f"translate({x}, {y}) rotate({rotation}) scale({scale})"

        g = dwg.g(transform=transform)
        dwg.add(g)

        # Get month data
        result = month['result']
        min_x, min_y, max_x, max_y = month['bounds']

        # Shift to origin
        shift_x = -min_x
        shift_y = -min_y

        # Create inner group with shift transform so outline and regions align
        inner_g = dwg.g(transform=f"translate({shift_x}, {shift_y})")
        g.add(inner_g)

        # Add regions to inner group (no manual shift needed, transform handles it)
        for r in result.regions:
            if r.poly.geom_type == 'MultiPolygon':
                for poly in r.poly.geoms:
                    coords = list(poly.exterior.coords)
                    if coords:
                        path_parts = [f"M {coords[0][0]} {coords[0][1]}"]
                        for cx, cy in coords[1:]:
                            path_parts.append(f"L {cx} {cy}")
                        path_parts.append("Z")
                        path_d = " ".join(path_parts)
                        inner_g.add(dwg.path(d=path_d, fill="none", stroke="gray", stroke_width=0.5))
            else:
                coords = list(r.poly.exterior.coords)
                if coords:
                    path_parts = [f"M {coords[0][0]} {coords[0][1]}"]
                    for cx, cy in coords[1:]:
                        path_parts.append(f"L {cx} {cy}")
                    path_parts.append("Z")
                    path_d = " ".join(path_parts)
                    inner_g.add(dwg.path(d=path_d, fill="none", stroke="gray", stroke_width=0.5))

        # Add outline to inner group
        inner_g.add(dwg.path(d=result.outline_path_svg, fill="none", stroke="navy", stroke_width=2))

        # Add labels with backgrounds to inner group
        for lab in result.labels:
            text_width = len(lab.text) * 36  # Tripled for larger font
            text_height = 60  # Tripled

            lx = lab.point.x
            ly = lab.point.y

            inner_g.add(dwg.rect(
                insert=(lx - text_width/2, ly - text_height/2),
                size=(text_width, text_height),
                fill="white",
                opacity=0.9
            ))

            inner_g.add(dwg.text(lab.text, insert=(lx, ly),
                          font_size="60px",  # Tripled from 20px
                          text_anchor="middle",
                          dominant_baseline="middle",
                          fill="black",
                          font_weight="bold"))

    # Save
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        f.write(dwg.tostring())

    print(f"✓ Year layout saved to {out_path}")
