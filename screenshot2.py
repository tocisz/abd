#!/usr/bin/env python
import argparse
import datetime
import os
import random
import shutil
import subprocess
import time

from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from deduplicate2 import deduplicate_svg
from make_font import count_glyphs_and_save_svg, find_glyphs_and_create_font
from md5counter import StringMD5Counter
from png2svg import crop, detect_pagesize
from svg2pdf2 import process_image_to_pdf_page


def adb_wrapper(func):
    """
    Wrapper function to handle common error handling for ADB operations.
    :param func: Function to wrap.
    """

    def wrapped_function(*args, **kwargs):
        try:
            adb_check = subprocess.run(
                ["adb", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if adb_check.returncode != 0:
                raise EnvironmentError("ADB is not installed or not added to PATH.")
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            print(f"Error while executing ADB command: {e}")
        except EnvironmentError as e:
            print(e)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    return wrapped_function


@adb_wrapper
def take_screenshot(directory, transport_id=None):
    """
    Take a screenshot on an Android device connected via ADB and save it to the specified directory.

    :param directory: Directory to save the screenshot
    :param transport_id: Optional ADB transport ID for the device
    """
    # Define the file paths
    device_file = "/sdcard/screenshot.png"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    local_file = os.path.join(directory, f"screenshot_{timestamp}.png")

    # Build adb command with optional transport ID
    def build_adb_cmd(cmd_parts):
        adb_cmd = ["adb"]
        if transport_id:
            adb_cmd.extend(["-t", transport_id])
        adb_cmd.extend(cmd_parts)
        return adb_cmd

    # Take the screenshot
    subprocess.run(build_adb_cmd(["shell", "screencap", "-p", device_file]), check=True)

    # Pull the screenshot file to the local machine
    subprocess.run(build_adb_cmd(["pull", device_file, local_file]), check=True)

    # Remove the screenshot file from the device
    subprocess.run(build_adb_cmd(["shell", "rm", device_file]), check=True)

    print(f"Screenshot saved to {local_file}")
    return local_file


@adb_wrapper
def press_volume_down(transport_id=None):
    """
    Simulate pressing the volume down key on an Android device connected via ADB.

    :param transport_id: Optional ADB transport ID for the device
    """
    # Build adb command with optional transport ID
    adb_cmd = ["adb"]
    if transport_id:
        adb_cmd.extend(["-t", transport_id])
    adb_cmd.extend(["shell", "input", "keyevent", "25"])

    # Simulate volume down key press
    subprocess.run(adb_cmd, check=True)
    print("Volume down key pressed.")


def crop_and_gather_svg_stats(count, png_file, svg_dir, crop_top, crop_bottom):
    """
    Crop the image and process it to PDF.
    """
    try:
        # Open the image
        with Image.open(png_file) as img:
            cropped_img = crop(img, crop_top, crop_bottom)
            count_glyphs_and_save_svg(png_file, svg_dir, cropped_img, count)
    except Exception as e:
        print(f"Error processing {png_file}: {e}")


def get_svg_dir(directory):
    return f"{directory}-svg"


def main():
    """
    Main function to take screenshots and convert them into PDF.
    """
    parser = argparse.ArgumentParser(
        description="Take screenshots convert them into PDF."
    )
    parser.add_argument(
        "directory",
        type=str,
        default="screenshots",
        help="Directory to save screenshots",
    )
    parser.add_argument(
        "-t",
        "--transport-id",
        type=str,
        default=None,
        help="ADB transport ID for the device",
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
        "--remove_svg",
        type=bool,
        default=True,
        help="Remove directory with converted SVG files.",
    )
    parser.add_argument(
        "--count_limit",
        type=int,
        default=10,
        help="Include glyphs more frequent than count limit into TTF",
    )
    args = parser.parse_args()

    pdf_canvas = None
    pagesize = None
    font_path = None
    output_pdf = f"{args.directory}.pdf"
    svg_dir = get_svg_dir(args.directory)

    # Create directories
    os.makedirs(args.directory, exist_ok=True)
    os.makedirs(svg_dir, exist_ok=True)

    count = StringMD5Counter()
    try:
        while True:
            png_file = take_screenshot(args.directory, args.transport_id)
            if pagesize is None:
                pagesize = detect_pagesize(png_file)
                pagesize = (pagesize[0], pagesize[1] - args.crop_top - args.crop_bottom)
                # pdf_canvas = canvas.Canvas(output_pdf, pagesize=pagesize)
            crop_and_gather_svg_stats(
                count, png_file, svg_dir, args.crop_top, args.crop_bottom
            )
            press_volume_down(args.transport_id)
            t = max(
                2, min(10, random.gauss(6, 2))
            )  # Random wait time with normal distribution
            print(f"Waiting for {t:.2f} seconds...")
            time.sleep(t)
    except KeyboardInterrupt:
        print("Program interrupted. Post-processing:")
        print("Creating TTF...")
        font_meta = find_glyphs_and_create_font(
            args.directory, svg_dir, count, args.count_limit, save_font_meta=False
        )

        print("Creating PDF...")
        pdf_canvas = canvas.Canvas(output_pdf, pagesize=pagesize)
        font_path = f"{args.directory}.ttf"
        # Register a custom font (or use a built-in font)
        pdfmetrics.registerFont(TTFont("F", font_path))
        svg_files = sorted(
            [f for f in os.listdir(svg_dir) if f.lower().endswith(".svg")]
        )
        for file_name in svg_files:
            svg_path = os.path.join(svg_dir, file_name)
            json_out_base = os.path.splitext(os.path.basename(file_name))[0]
            json_path = os.path.join(svg_dir, f"{json_out_base}.json")
            try:
                with open(svg_path, "r") as f:
                    # Overwrite existing SVG file
                    deduplicate_svg(f.read(), svg_path, font_meta, json_path)
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
            if pagesize:
                process_image_to_pdf_page(pdf_canvas, pagesize[1], svg_path, json_path)
            else:
                raise Exception("Couldn't detect page size. Aborting.")
        pdf_canvas.save()
    finally:
        if args.remove_svg:
            if os.path.exists(svg_dir):
                shutil.rmtree(svg_dir)
                print("Temporary directory removed.")
        if font_path and os.path.exists(font_path):
            os.unlink(font_path)
            print("Font removed.")


if __name__ == "__main__":
    main()
