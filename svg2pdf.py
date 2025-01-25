#!/usr/bin/env python
import os
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
import argparse

# Function to convert SVG images to a PDF
def convert_to_pdf(directory, output_pdf):
    # Get a sorted list of SVG files in the directory
    svg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.svg')])

    if not svg_files:
        print("No SVG files found in the directory.")
        return

    pagesize = detect_pagesize(directory, svg_files[0])
    print(f"Detected page size: {pagesize}")

    # Create a PDF
    pdf_canvas = canvas.Canvas(output_pdf, pagesize=pagesize)

    for file_name in svg_files:
        print(file_name)
        file_path = os.path.join(directory, file_name)
        try:
            process_image_to_pdf_page(pdf_canvas, file_path)

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    # Save the PDF
    pdf_canvas.save()

    print(f"PDF created successfully: {output_pdf}")

# Function to detect the page size based on the first image
def detect_pagesize(directory, file_name):
    file_path = os.path.join(directory, file_name)
    drawing = svg2rlg(file_path)
    return (drawing.width, drawing.height)

def process_image_to_pdf_page(pdf_canvas, svg_file):
    # Draw the image on the PDF
    drawing = svg2rlg(svg_file)
    renderPDF.draw(drawing, pdf_canvas, 0, 0)
    pdf_canvas.showPage()  # Add a new page

# Main function to parse arguments and call the processing function
def main():
    parser = argparse.ArgumentParser(description="Convert SVG images to a PDF.")
    parser.add_argument("input_directory", type=str, help="Path to the input directory containing SVG files.")
    args = parser.parse_args()

    output_pdf = f"{args.input_directory}.pdf"
    convert_to_pdf(args.input_directory, output_pdf)

if __name__ == "__main__":
    main()
