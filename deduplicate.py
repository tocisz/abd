#!/usr/bin/env python
import os
import argparse
import re
import xml.etree.ElementTree as ET

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NAMESPACE)
ET.register_namespace("xlink", XLINK_NAMESPACE)

# Function to convert SVG images to a PDF
def deduplicate(directory, output_dir):
    # Get a sorted list of SVG files in the directory
    svg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.svg')])

    if not svg_files:
        print("No SVG files found in the directory.")
        return

    for file_name in svg_files:
        print(file_name)
        file_path = os.path.join(directory, file_name)
        out_path = os.path.join(output_dir, file_name)
        try:
            with open(file_path, "r") as f:
                deduplicate_svg(f.read(), out_path)

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

def deduplicate_svg(in_svg, out_file):
    path_dict = dict()
    input_root = ET.fromstring(in_svg)
    width = input_root.get('width')
    height = input_root.get('height')
    print(f"{width} x {height}")
    for path_element in input_root.findall('.//svg:path', {"svg":SVG_NAMESPACE}):
        d = path_element.get('d').rstrip()  # Extract path data
        t = extract_translate_coordinates(path_element.get('transform'))
        if d not in path_dict:
            path_dict[d] = [t]
        else:
            path_dict[d].append(t)
    out_svg = create_svg(width, height, path_dict)
    tree = ET.ElementTree(out_svg)
    with open(out_file, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

def create_svg(width, height, paths:dict):
    count = 1
    svg = ET.Element("svg", attrib={
        "xmlns": SVG_NAMESPACE,
        "version": "1.1",
        "width": width,
        "height": height
    })
    defs = ET.SubElement(svg, "defs")
    for d, uses in paths.items():
        if len(uses) == 1:
            make_path(svg, d, uses[0])
        else:
            make_path(defs, d, id=count)
            for c in uses:
                ET.SubElement(svg,"use", attrib={
                    "x": str(c[0]),
                    "y": str(c[1]),
                    f"{{{XLINK_NAMESPACE}}}href": f"#{count}"
                })
            count += 1
    return svg

def make_path(root, d, coord=None, id=None):
    p = ET.SubElement(root, "path", attrib={
        "d": d,
        "fill": "#000000"
    })
    if id:
        p.attrib["id"] = str(id)
    if coord:
        p.attrib["transform"] = f"translate({coord[0]},{coord[1]})"

def extract_translate_coordinates(transform_expression):
    # Regular expression to match translate(x, y)
    pattern = r"translate\(([-+]?\d*\.?\d+),\s*([-+]?\d*\.?\d+)\)"
    match = re.search(pattern, transform_expression)
    
    if match:
        # Extract and convert the coordinates to floats
        x, y = int(match.group(1)), int(match.group(2))
        return x, y
    return None  # Return None if no match is found

# Main function to parse arguments and call the processing function
def main():
    parser = argparse.ArgumentParser(description="Convert SVG images to a PDF.")
    parser.add_argument("input_directory", type=str, help="Path to the input directory containing SVG files.")
    parser.add_argument("output_directory", type=str, help="Path to the input directory containing SVG files.")
    args = parser.parse_args()
    os.makedirs(args.output_directory, exist_ok=True)
    deduplicate(args.input_directory, args.output_directory)

if __name__ == "__main__":
    main()
