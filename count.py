#!/usr/bin/env python
import os
import argparse
import xml.etree.ElementTree as ET
import io
import vtracer
from md5counter import StringMD5Counter
from png2svg import detect_pagesize, crop, round_svg_numbers
from PIL import Image
import json

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NAMESPACE)
ET.register_namespace("xlink", XLINK_NAMESPACE)

def crop_and_do_shape_stats(directory, svg_dir, crop_top, crop_bottom, limit):
    # Get a sorted list of PNG files in the directory
    png_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.png')])

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

    to_ttf = set([k for (k,v) in count.md5_count.items() if v >= limit])
    glyphs = find_glyphs(svg_dir, to_ttf)
    with open(f"{directory}-glyphs.json", 'w') as file:
        json.dump(glyphs, file)

SPLINE = {
    "mode":'spline',
    "corner_threshold":75,
    "filter_speckle":3
}
POLYGON = {
    "mode":'polygon',
    "filter_speckle":3
}

def count_glyphs_and_save_svg(png_file, svg_dir, img, count:StringMD5Counter, mode=POLYGON):
    img = img.convert("L")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")

    # Save image as SVG file to draw in PDF
    img_byte_arr.seek(0)
    svg = vtracer.convert_raw_image_to_svg(img_byte_arr.getvalue(),
                                             img_format='PNG',
                                             colormode='binary',
                                             **mode)
    svg = round_svg_numbers(svg)
    input_root = ET.fromstring(svg)
    for path_element in input_root.findall('.//svg:path', {"svg":SVG_NAMESPACE}):
        d = path_element.get('d').rstrip()  # Extract path data
        count.add_string(d)
    file_name = os.path.splitext(os.path.basename(png_file))[0]
    svg_file = os.path.join(svg_dir, f"{file_name}.svg")
    with open(svg_file, "wb") as f:
        tree = ET.ElementTree(input_root)
        tree.write(f, encoding="utf-8", xml_declaration=True)

def find_glyphs(directory, to_ttf:set):
    result = []
    svg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.svg')])
    for file_name in svg_files:
        file_path = os.path.join(directory, file_name)
        try:
            # Open the image
            tree = ET.parse(file_path)
            input_root = tree.getroot()
            for path_element in input_root.findall('.//svg:path', {"svg":SVG_NAMESPACE}):
                d = path_element.get('d').rstrip()  # Extract path data
                h = StringMD5Counter.hash(d)
                if h in to_ttf:
                    result.append(d)
                    to_ttf.remove(h)
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
        if len(to_ttf) == 0:
            break
    return result

def get_svg_dir(directory):
    return f"{directory}-svg"

def main():
    """
    Main function to take screenshots and count stats
    """
    parser = argparse.ArgumentParser(description="Make font stats")
    parser.add_argument("directory", type=str, default="screenshots", help="Directory with screenshots")
    parser.add_argument("--crop_top", type=int, default=150, help="Number of pixels to crop from the top of each image.")
    parser.add_argument("--crop_bottom", type=int, default=150, help="Number of pixels to crop from the bottom of each image.")
    parser.add_argument("--count_limit", type=int, default=150, help="Include glyphs more frequent than count limit into TTF")
    args = parser.parse_args()

    svg_dir = get_svg_dir(args.directory)
    # Create directories
    os.makedirs(svg_dir, exist_ok=True)

    crop_and_do_shape_stats(args.directory, svg_dir, args.crop_top, args.crop_bottom, args.count_limit)

if __name__ == "__main__":
    main()

# >>> from md5counter import *
# >>> cnt = StringMD5Counter.load_from_file('maslowska-magiczna_rana.json')
# >>> sum([v for v in cnt.md5_count.values() if v >= 50])/sum(cnt.md5_count.values())*100
# 97.58197505443745
# >>> sum([v for v in cnt.md5_count.values() if v >= 100])/sum(cnt.md5_count.values())*100
# 96.53468052733717
# >>> sum([v for v in cnt.md5_count.values() if v >= 1000])/sum(cnt.md5_count.values())*100
# 83.69564227079329
# >>> sum([v for v in cnt.md5_count.values() if v >= 500])/sum(cnt.md5_count.values())*100
# 94.4596798440219
# >>> sum([v for v in cnt.md5_count.values() if v >= 700])/sum(cnt.md5_count.values())*100
# 90.88730764675334
# >>> len([v for v in cnt.md5_count.values() if v >= 700])
# 99