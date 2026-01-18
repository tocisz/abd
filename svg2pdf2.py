#!/usr/bin/env python
import argparse
import json
import os

from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg


# Function to convert SVG images to a PDF
def convert_to_pdf(directory, output_pdf):
    # Get a sorted list of SVG files in the directory
    svg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith(".svg")])

    if not svg_files:
        print("No SVG files found in the directory.")
        return

    pagesize = detect_pagesize(directory, svg_files[0])
    print(f"Detected page size: {pagesize}")

    font_path = f"{directory}.ttf"
    # Register a custom font (or use a built-in font)
    pdfmetrics.registerFont(TTFont("F", font_path))

    # Create a PDF
    pdf_canvas = canvas.Canvas(output_pdf, pagesize=pagesize)
    for svg_file in svg_files:
        print(svg_file)
        svg_path = os.path.join(directory, svg_file)
        fn_base = os.path.splitext(os.path.basename(svg_file))[0]
        json_path = os.path.join(directory, f"{fn_base}.json")
        try:
            process_image_to_pdf_page(pdf_canvas, pagesize[1], svg_path, json_path)

        except Exception as e:
            print(f"Error processing {svg_file}: {e}")

    # Save the PDF
    pdf_canvas.save()

    print(f"PDF created successfully: {output_pdf}")


# Function to detect the page size based on the first image
def detect_pagesize(directory, svg_file):
    file_path = os.path.join(directory, svg_file)
    drawing = svg2rlg(file_path)
    if drawing:
        return (drawing.width, drawing.height)
    else:
        raise Exception("Couldn't process drawing")


def process_image_to_pdf_page(pdf_canvas: canvas.Canvas, height, svg_path, json_path):
    # Draw the image on the PDF
    drawing = svg2rlg(svg_path)
    if drawing:
        renderPDF.draw(drawing, pdf_canvas, 0, 0)
    else:
        raise Exception("Couldn't process drawing")
    render_text(pdf_canvas, height, json_path)
    pdf_canvas.showPage()  # Add a new page


def render_text(pdf_canvas: canvas.Canvas, height, json_path):
    with open(json_path, "r") as f:
        font_uses = json.load(f)
    text = pdf_canvas.beginText()
    text.setFont("F", 100)
    if len(font_uses) > 0:
        code_point, x, y = font_uses[0]
        text.setTextOrigin(x, height - y)
        text.textOut(chr(code_point))
        px, py = x, y
        for code_point, x, y in font_uses[1:]:
            text.moveCursor(x - px, y - py)
            text.textOut(chr(code_point))
            px, py = x, y
    pdf_canvas.drawText(text)


# Main function to parse arguments and call the processing function
def main():
    parser = argparse.ArgumentParser(description="Convert SVG images to a PDF.")
    parser.add_argument(
        "input_directory",
        type=str,
        help="Path to the input directory containing SVG files.",
    )
    args = parser.parse_args()

    output_pdf = f"{args.input_directory}.pdf"
    convert_to_pdf(args.input_directory, output_pdf)


if __name__ == "__main__":
    main()
