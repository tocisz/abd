#!/usr/bin/env python
import re
from typing import Tuple

from PIL import Image


# Function to detect the page size based on the first image
def detect_pagesize(file_path) -> Tuple[int, int]:
    # Open the image
    with Image.open(file_path) as img:
        width, height = img.size
    print(f"Pages size is {width} x {height}")
    return (width, height)


def crop(img, crop_top, crop_bottom):
    width, height = img.size
    return img.crop((0, crop_top, width, height - crop_bottom))


def round_svg_numbers(svg_str):
    pattern = r"([MC ])([-+]?\d*\.\d+)"

    # Define a replacement function that rounds the matched number
    def round_match(match):
        number = float(match.group(2))  # Convert matched string to float
        rounded_number = round(number, 2)  # Round to 2 decimal places
        return match.group(1) + ("{:.2f}".format(rounded_number)).rstrip("0").rstrip(
            "."
        )  # Remove trailing zeros and dot if necessary

    return re.sub(pattern, round_match, svg_str)
