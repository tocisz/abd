#!/usr/bin/env python
import os
import subprocess
import datetime
import time
import random
import argparse
import shutil
from PIL import Image
from reportlab.pdfgen import canvas
from png2svg import process_image_to_svg, detect_pagesize, crop
from svg2pdf import process_image_to_pdf_page

def adb_wrapper(func):
    """
    Wrapper function to handle common error handling for ADB operations.
    :param func: Function to wrap.
    """
    def wrapped_function(*args, **kwargs):
        try:
            adb_check = subprocess.run(["adb", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
def take_screenshot(directory):
    """
    Take a screenshot on an Android device connected via ADB and save it to the specified directory.
    """
    # Define the file paths
    device_file = "/sdcard/screenshot.png"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    local_file = os.path.join(directory, f"screenshot_{timestamp}.png")

    # Take the screenshot
    subprocess.run(["adb", "shell", "screencap", "-p", device_file], check=True)

    # Pull the screenshot file to the local machine
    subprocess.run(["adb", "pull", device_file, local_file], check=True)

    # Remove the screenshot file from the device
    subprocess.run(["adb", "shell", "rm", device_file], check=True)

    print(f"Screenshot saved to {local_file}")
    return local_file

@adb_wrapper
def press_volume_down():
    """
    Simulate pressing the volume down key on an Android device connected via ADB.
    """
    # Simulate volume down key press
    subprocess.run(["adb", "shell", "input", "keyevent", "25"], check=True)
    print("Volume down key pressed.")

def crop_and_append_to_pdf(pdf_canvas, png_file, svg_dir, crop_top, crop_bottom):
    """
    Crop the image and process it to PDF.
    """
    try:
        # Open the image
        with Image.open(png_file) as img:
            cropped_img = crop(img, crop_top, crop_bottom)
            svg_file = process_image_to_svg(svg_dir, png_file, cropped_img)
            process_image_to_pdf_page(pdf_canvas, svg_file)
    except Exception as e:
        print(f"Error processing {png_file}: {e}")

def get_svg_dir(directory):
    return f"{directory}-svg"

def main():
    """
    Main function to take screenshots and convert them into PDF.
    """
    parser = argparse.ArgumentParser(description="Take screenshots convert them into PDF.")
    parser.add_argument("directory", type=str, default="screenshots", help="Directory to save screenshots")
    parser.add_argument("--crop_top", type=int, default=150, help="Number of pixels to crop from the top of each image.")
    parser.add_argument("--crop_bottom", type=int, default=150, help="Number of pixels to crop from the bottom of each image.")
    parser.add_argument("--remove_svg", type=bool, default=False, help="Remove directory with converted SVG files.")
    args = parser.parse_args()

    pdf_canvas = None
    pagesize = None
    output_pdf = f"{args.directory}.pdf"
    svg_dir = get_svg_dir(args.directory)

    # Create directories
    os.makedirs(args.directory, exist_ok=True)
    os.makedirs(svg_dir, exist_ok=True)

    try:
        while True:
            png_file = take_screenshot(args.directory)
            if pagesize is None:
                pagesize = detect_pagesize(png_file)
                pagesize = (pagesize[0], pagesize[1] - args.crop_top - args.crop_bottom)
                pdf_canvas = canvas.Canvas(output_pdf, pagesize=pagesize)
            crop_and_append_to_pdf(pdf_canvas, png_file, svg_dir, args.crop_top, args.crop_bottom)
            press_volume_down()
            t = max(2, min(10, random.gauss(6, 2)))  # Random wait time with normal distribution
            print(f"Waiting for {t:.2f} seconds...")
            time.sleep(t)
    except KeyboardInterrupt:
        print("Program interrupted. Cleaning up...")
    finally:
        if pdf_canvas:
            pdf_canvas.save()
        if args.remove_svg:
            if os.path.exists(svg_dir):
                shutil.rmtree(svg_dir)
            print("Temporary directory removed.")

if __name__ == "__main__":
    main()
