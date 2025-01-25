#!/usr/bin/env python
import os
import argparse
import io
import re
from PIL import Image
import vtracer
import xml.etree.ElementTree as ET
from deduplicate import deduplicate_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NAMESPACE)
ET.register_namespace("xlink", XLINK_NAMESPACE)

# Function to detect the page size based on the first image
def detect_pagesize(file_path):
    # Open the image
    with Image.open(file_path) as img:
        width, height = img.size
    print(f"Pages size is {width} x {height}")
    return (width, height)

def crop_and_convert_to_svg(directory, svg_dir, crop_top, crop_bottom):
    # Get a sorted list of PNG files in the directory
    png_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.png')])

    if not png_files:
        print("No PNG files found in the directory.")
        return

    pagesize = detect_pagesize(os.path.join(directory, png_files[0]))
    pagesize = (pagesize[0], pagesize[1] - crop_top - crop_bottom)
    print(f"Detected page size: {pagesize}")

    for file_name in png_files:
        print(file_name)
        file_path = os.path.join(directory, file_name)
        try:
            # Open the image
            with Image.open(file_path) as img:
                cropped_img = crop(img, crop_top, crop_bottom)
                process_image_to_svg(svg_dir, file_path, cropped_img)

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

def crop(img, crop_top, crop_bottom):
    width, height = img.size
    return img.crop((0, crop_top, width, height - crop_bottom))

SPLINE = {
    "mode":'spline',
    "corner_threshold":75,
    "filter_speckle":3
}
PLOYGON = {
    "mode":'polygon',
    "filter_speckle":3
}

def process_image_to_svg(svg_dir, png_file, img, mode=PLOYGON):
    img = img.convert("L")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")

    # Save image as SVG file to draw in PDF
    file_name = os.path.splitext(os.path.basename(png_file))[0]
    svg_file = os.path.join(svg_dir, f"{file_name}.svg")
    img_byte_arr.seek(0)
    svg = vtracer.convert_raw_image_to_svg(img_byte_arr.getvalue(),
                                             img_format='PNG',
                                             colormode='binary',
                                             **mode)
    img_byte_arr.close()
    svg = round_svg_numbers(svg)
    deduplicate_svg(svg, svg_file)
    return svg_file

def round_svg_numbers(svg_str):
    pattern = r"([MC ])([-+]?\d*\.\d+)"
    # Define a replacement function that rounds the matched number
    def round_match(match):
        number = float(match.group(2))  # Convert matched string to float
        rounded_number = round(number, 2)  # Round to 2 decimal places
        return match.group(1) + ("{:.2f}".format(rounded_number)).rstrip('0').rstrip('.')  # Remove trailing zeros and dot if necessary
    return re.sub(pattern, round_match, svg_str)

def get_svg_dir(directory):
    return f"{directory}-svg"

def main():
    """
    Main function to take screenshots and convert them into SVG.
    """
    parser = argparse.ArgumentParser(description="Convert screenshots to SVG.")
    parser.add_argument("directory", type=str, default="screenshots", help="Directory with screenshots")
    parser.add_argument("--crop_top", type=int, default=150, help="Number of pixels to crop from the top of each image.")
    parser.add_argument("--crop_bottom", type=int, default=150, help="Number of pixels to crop from the bottom of each image.")
    args = parser.parse_args()

    svg_dir = get_svg_dir(args.directory)

    # Create directories
    os.makedirs(svg_dir, exist_ok=True)

    crop_and_convert_to_svg(args.directory, svg_dir, args.crop_top, args.crop_bottom)

if __name__ == "__main__":
    main()
