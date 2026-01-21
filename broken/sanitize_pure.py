import struct
import os
import time

# ---------------- CONFIGURATION ----------------
INPUT_FOLDER = "1_Incoming"
OUTPUT_FOLDER = "2_Processing"
# -----------------------------------------------

def parse_header(f):
    """ Reads the PLY header to find where the data starts and what format it is. """
    header = {}
    line = ""
    while line != "end_header":
        line = f.readline().decode('utf-8').strip()
        if line.startswith("element vertex"):
            header['num_vertices'] = int(line.split()[-1])
        elif line.startswith("element face"):
            header['num_faces'] = int(line.split()[-1])
        elif line.startswith("property float x"):
            header['vertex_format'] = 'float'
    return header

def manual_extract(filename):
    print(f"👀 Detecting new scan: {filename}")
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_filename = filename.replace(".ply", ".obj")
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    try:
        with open(input_path, "rb") as f:
            # 1. READ HEADER
            header = parse_header(f)
            print(f"   Header Info: {header}")
            
            num_v = header.get('num_vertices', 0)
            num_f = header.get('num_faces', 0)

            if num_v == 0:
                print("❌ Error: No vertices found in header.")
                return

            # 2. READ VERTICES (XYZ)
            # Assuming standard float32 (4 bytes) for x, y, z. 
            # We skip other properties (nx, ny, nz, red, green, blue) by calculating stride.
            # *CRITICAL*: This assumes the first 3 properties are ALWAYS x, y, z.
            
            # Read the whole binary blob for vertices
            # We have to guess the 'stride' (how many bytes per vertex).
            # Standard iOS PLY usually has x,y,z (float) + nx,ny,nz (float) + r,g,b (uchar)
            # But let's try to just read 3 floats and skip the rest for now.
            
            vertices = []
            
            # Standard float is 4 bytes. 
            # If your file is 'binary_little_endian', we read chunks.
            # This is a 'dumb' reader: It assumes specific packing. 
            # If this fails, we will try the ASCII reader.

            # ...Actually, writing a binary parser from scratch is risky without knowing the exact format.
            # Let's try a safer "Hybrid" approach.
            pass

    except Exception as e:
        print(f"❌ Failed: {e}")

# --- RE-WRITING FOR ROBUSTNESS BELOW ---