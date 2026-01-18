#!/usr/bin/env python
import argparse
import io
import json
import os
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

import fontforge
import svgelements
import vtracer
from PIL import Image

from md5counter import StringMD5Counter
from png2svg import crop, detect_pagesize, round_svg_numbers

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NAMESPACE)
ET.register_namespace("xlink", XLINK_NAMESPACE)


def crop_and_do_shape_stats(directory, svg_dir, crop_top, crop_bottom, limit):
    # Get a sorted list of PNG files in the directory
    png_files = sorted([f for f in os.listdir(directory) if f.lower().endswith(".png")])

    if not png_files:
        print("No PNG files found in the directory.")
        return

    pagesize = detect_pagesize(os.path.join(directory, png_files[0]))
    pagesize = (pagesize[0], pagesize[1] - crop_top - crop_bottom)
    print(f"Detected page size: {pagesize}")

    count = StringMD5Counter()
    for file_name in png_files:
        print(file_name)
        file_path = os.path.join(directory, file_name)
        try:
            # Open the image
            with Image.open(file_path) as img:
                cropped_img = crop(img, crop_top, crop_bottom)
                count_glyphs_and_save_svg(file_path, svg_dir, cropped_img, count)
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    count.dump_to_file(f"{directory}.json")
    find_glyphs_and_create_font(directory, svg_dir, count, limit)


def find_glyphs_and_create_font(directory, svg_dir, count, limit, save_font_meta=True):
    to_ttf = set([k for (k, v) in count.md5_count.items() if v >= limit])
    glyphs = find_glyphs(svg_dir, to_ttf)
    return create_font_from_memory_svgs(glyphs, f"{directory}.ttf", save_font_meta)


SPLINE = {"mode": "spline", "corner_threshold": 75, "filter_speckle": 3}
POLYGON = {"mode": "polygon", "filter_speckle": 3}


def count_glyphs_and_save_svg(
    png_file, svg_dir, img, count: StringMD5Counter, mode=POLYGON
):
    img = img.convert("L")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")

    # Save image as SVG file to draw in PDF
    img_byte_arr.seek(0)
    svg = vtracer.convert_raw_image_to_svg(
        img_byte_arr.getvalue(), img_format="PNG", colormode="binary", **mode
    )
    svg = round_svg_numbers(svg)
    input_root = ET.fromstring(svg)
    for path_element in input_root.findall(".//svg:path", {"svg": SVG_NAMESPACE}):
        d = path_element.get("d")
        if d is not None:
            d = d.rstrip()  # Extract path data
            count.add_string(d)
    file_name = os.path.splitext(os.path.basename(png_file))[0]
    svg_file = os.path.join(svg_dir, f"{file_name}.svg")
    with open(svg_file, "wb") as f:
        tree = ET.ElementTree(input_root)
        tree.write(f, encoding="utf-8", xml_declaration=True)


def find_glyphs(directory, to_ttf: set):
    result = []
    svg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith(".svg")])
    for file_name in svg_files:
        file_path = os.path.join(directory, file_name)
        try:
            # Open the image
            tree = ET.parse(file_path)
            input_root = tree.getroot()
            for path_element in input_root.findall(
                ".//svg:path", {"svg": SVG_NAMESPACE}
            ):
                d = path_element.get("d")
                if d is not None:
                    d = d.rstrip()  # Extract path data
                    h = StringMD5Counter.hash(d)
                    if h in to_ttf:
                        result.append(d)
                        to_ttf.remove(h)
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
        if len(to_ttf) == 0:
            break
    return result


def create_font_from_memory_svgs(glyphs, output_font_path, save_font_meta=True):
    font = fontforge.font()
    font.encoding = "UnicodeFull"
    font.em = 1000
    font.ascent = 0
    font.descent = 1000
    code_point = ord(" ") + 1

    font_dict = dict()

    for d in glyphs:
        dbox = svgelements.Path(d).bbox()
        if not dbox:
            print(f"Can't process path {d}")
            continue
        if not is_within_range(*dbox):
            print(f"Path {d} is too large")
            continue

        glyph = font.createChar(code_point)
        # Use temporary file for in-memory SVG
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=True) as temp_svg:
            make_svg(d, dbox, temp_svg)
            temp_svg.flush()
            glyph.importOutlines(temp_svg.name)

        # Set side bearings and fix direction
        glyph.left_side_bearing = 0
        glyph.right_side_bearing = 0
        glyph.width = 0  # assuming height 1000
        glyph.correctDirection()

        hash = StringMD5Counter.hash(d)
        font_dict[hash] = {"code_point": code_point, "bbox": dbox}

        code_point += 1
        while not is_printable(code_point):
            code_point += 1

    # Generate the font
    font.generate(output_font_path)
    print(f"Font saved to {output_font_path}")
    file_name = os.path.splitext(os.path.basename(output_font_path))[0]
    if save_font_meta:
        font_dict_path = os.path.join(
            os.path.dirname(output_font_path), f"{file_name}-meta.json"
        )
        with open(font_dict_path, "w") as f:
            json.dump(font_dict, f)
    return font_dict


def is_within_range(xmin, ymin, xmax, ymax):
    return xmax - xmin <= 100 and ymax - ymin <= 100


def make_svg(d, dbox, svg_file):
    xmin, ymin, _, _ = dbox
    svg = ET.Element(
        "svg",
        attrib={
            "xmlns": SVG_NAMESPACE,
            "version": "1.1",
            "viewBox": f"{xmin} {ymin} {xmin + 100} {ymin + 100}",
        },
    )
    ET.SubElement(svg, "path", attrib={"d": d, "fill": "#000000"})
    tree = ET.ElementTree(svg)
    tree.write(svg_file, encoding="utf-8", xml_declaration=True)


def is_printable(n):
    cat = unicodedata.category(chr(n))
    return cat[0] in ["L", "N", "P", "S"]


def get_svg_dir(directory):
    return f"{directory}-svg"


def main():
    """
    Main function to make font from screenshots
    """
    parser = argparse.ArgumentParser(description="Make font from screenshots stats")
    parser.add_argument(
        "directory", type=str, default="screenshots", help="Directory with screenshots"
    )
    parser.add_argument(
        "--crop_top",
        type=int,
        default=150,
        help="Number of pixels to crop from the top of each image.",
    )
    parser.add_argument(
        "--crop_bottom",
        type=int,
        default=150,
        help="Number of pixels to crop from the bottom of each image.",
    )
    parser.add_argument(
        "--count_limit",
        type=int,
        default=10,
        help="Include glyphs more frequent than count limit into TTF",
    )
    args = parser.parse_args()

    svg_dir = get_svg_dir(args.directory)
    # Create directories
    os.makedirs(svg_dir, exist_ok=True)

    crop_and_do_shape_stats(
        args.directory, svg_dir, args.crop_top, args.crop_bottom, args.count_limit
    )


if __name__ == "__main__":
    main()
