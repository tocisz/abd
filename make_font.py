import fontforge
import tempfile
import json
import svgelements
import xml.etree.ElementTree as ET
import unicodedata
import os
from md5counter import StringMD5Counter

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NAMESPACE)

def create_font_from_memory_svgs(glyphs, output_font_path):
    font = fontforge.font()
    font.encoding = "UnicodeFull"
    font.em = 1000
    code_point = ord(' ')+1

    font_dict = dict()

    for d in glyphs:
        if not is_within_range(d):
            print(f"Path {d} is too large")
            continue

        glyph = font.createChar(code_point)
        # Use temporary file for in-memory SVG
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=True) as temp_svg:
            make_svg(d, temp_svg)
            temp_svg.flush()
            glyph.importOutlines(temp_svg.name)

        # Set side bearings and fix direction
        glyph.left_side_bearing = 0
        glyph.right_side_bearing = 0
        glyph.width = 1000 # assuming height 1000
        glyph.correctDirection()

        hash = StringMD5Counter.hash(d)
        bbox = svgelements.Path(d).bbox()
        font_dict[hash] = {
            'code_point': code_point,
            'bbox': bbox
        }

        code_point += 1
        while not is_printable(code_point):
            code_point += 1

    # Generate the font
    font.generate(output_font_path)
    print(f"Font saved to {output_font_path}")
    file_name = os.path.splitext(os.path.basename(output_font_path))[0]
    font_dict_path = os.path.join(os.path.dirname(output_font_path), f"{file_name}-meta.json")
    with open(font_dict_path, 'w') as f:
        json.dump(font_dict, f)

def is_within_range(d):
    xmin, ymin, xmax, ymax = svgelements.Path(d).bbox()
    return xmin >= -50 and xmax <= 50 and ymin >= 0 and ymax <= 100

def make_svg(d, svg_file):
    svg = ET.Element("svg", attrib={
        "xmlns": SVG_NAMESPACE,
        "version": "1.1",
        "viewBox": "-50 0 50 100"
    })
    ET.SubElement(svg, "path", attrib={
        "d": d,
        "fill": "#000000"
    })
    tree = ET.ElementTree(svg)
    tree.write(svg_file, encoding="utf-8", xml_declaration=True)

def is_printable(n):
    cat = unicodedata.category(chr(n))
    return cat[0] in ['L','N','P','S']

# Paths seem to be scaled according to viewBox
# (A and d are roughly the same size, despite viewBox very different)
# looks like height is assumed to be 1000 and width is scaled proportionally

# SVG coodrinates 1) X left to right 2) Y top to bottom

# OK, one thing left to understand: how to scale letters from font in order for them to have the same size?

# Maybe easiest would be to filter out everything greater than 100 and use font size of 100. In that case all glyphs need to be scaled x10.
# So viewbox is always "0 0 100 100" ? hmm IDK sample path goes below 0 in Y dimension
# 1000 ?

with open('maslowska-magiczna_rana-glyphs.json', 'r') as f:
    svg_data_map = json.load(f)
output_path = "maslowska-magiczna_rana.ttf"
create_font_from_memory_svgs(svg_data_map, output_path)
