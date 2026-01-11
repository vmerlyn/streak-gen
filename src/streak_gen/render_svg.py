import svgwrite
from .types import Region, Label

def render_letter_svg(page, margin, outline_path_svg, regions, labels):
    w, h = (612, 792)
    dwg = svgwrite.Drawing(size=(w, h))
    dwg.add(dwg.rect(insert=(0, 0), size=(w, h), fill="white"))
    g = dwg.g()
    dwg.add(g)
    for r in regions:
        pass
    g.add(dwg.path(d=outline_path_svg, fill="none", stroke="black", stroke_width=4))
    for lab in labels:
        g.add(dwg.text(lab.text, insert=(lab.point.x, lab.point.y)))
    return dwg.tostring()
