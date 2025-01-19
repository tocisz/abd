#!/usr/bin/env python
import os
from PIL import Image
from reportlab.pdfgen import canvas
import argparse

tmp_dir = "tmp"

# Function to crop images and convert them to a PDF
def crop_and_convert_to_pdf(directory, output_pdf, crop_top, crop_bottom):
    global tmp_dir
    # Get a sorted list of PNG files in the directory
    png_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.png')])

    if not png_files:
        print("No PNG files found in the directory.")
        return

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    pagesize = detect_pagesize(directory, png_files[0])
    pagesize = (pagesize[0], pagesize[1] - crop_top - crop_bottom)
    print(f"Detected page size: {pagesize}")

    # Create a PDF
    c = canvas.Canvas(output_pdf, pagesize=pagesize)

    for file_name in png_files:
        print(file_name)
        file_path = os.path.join(directory, file_name)
        try:
            # Open the image
            with Image.open(file_path) as img:
                cropped_img = crop(img, crop_top, crop_bottom)
                process_image_to_pdf_page(c, file_name, cropped_img, pagesize)

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    # Save the PDF
    c.save()

    # Remove directory with temporary files
    for f in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)

    print(f"PDF created successfully: {output_pdf}")

def crop(img, crop_top, crop_bottom):
    width, height = img.size
    return img.crop((0, crop_top, width, height - crop_bottom))

# Function to detect the page size based on the first image
def detect_pagesize(directory, file_name):
    file_path = os.path.join(directory, file_name)
    # Open the image
    with Image.open(file_path) as img:
        width, height = img.size
    return (width, height)

def process_image_to_pdf_page(c, file_name, img, pagesize):
    global tmp_dir
    # Convert PIL image to RGB mode (required for saving)
    img = img.convert("L")

    # Save image as a temporary file to draw in PDF
    temp_file = os.path.join(tmp_dir, f"{file_name}.jpg")
    img.save(temp_file, "JPEG")

    # Draw the image on the PDF
    c.drawImage(temp_file, 0, 0)
    c.showPage()  # Add a new page

# Main function to parse arguments and call the processing function
def main():
    parser = argparse.ArgumentParser(description="Crop PNG images and convert them to a PDF.")
    parser.add_argument("input_directory", type=str, help="Path to the input directory containing PNG files.")
    parser.add_argument("output_file", type=str, help="Path to the output PDF file.")
    parser.add_argument("--crop_top", type=int, default=150, help="Number of pixels to crop from the top of each image.")
    parser.add_argument("--crop_bottom", type=int, default=150, help="Number of pixels to crop from the bottom of each image.")
    args = parser.parse_args()

    crop_and_convert_to_pdf(args.input_directory, args.output_file, args.crop_top, args.crop_bottom)

if __name__ == "__main__":
    main()
