from plyfile import PlyData
import os
import time

# ---------------- CONFIGURATION ----------------
INPUT_FOLDER = "1_Incoming"
OUTPUT_FOLDER = "2_Processing"
# -----------------------------------------------

def surgical_extract(filename):
    print(f"👀 Detecting new scan: {filename}")
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_filename = filename.replace(".ply", ".obj")
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    try:
        # 1. Read Raw Data (No validation, just bytes)
        plydata = PlyData.read(input_path)
        
        # 2. Extract Vertices (Points)
        # We look for the 'vertex' element
        vertices = plydata['vertex']
        print(f"   Found {len(vertices)} vertices")
        
        # 3. Extract Faces (Triangles)
        # We look for the 'face' element
        try:
            faces = plydata['face']
            print(f"   Found {len(faces)} faces")
            has_faces = True
        except:
            print("   ⚠️ No faces found (Point Cloud only)")
            has_faces = False

        # 4. Write Manual OBJ
        # We write the text file line-by-line to ensure it is perfect
        with open(output_path, "w") as f:
            f.write(f"# Rhinovate Surgical Fix for {filename}\n")
            
            # Write Vertices (v x y z)
            # We explicitly ignore color properties (red, green, blue) here
            for v in vertices:
                f.write(f"v {v['x']} {v['y']} {v['z']}\n")
            
            # Write Faces (f v1 v2 v3)
            # PLY is 0-indexed, OBJ is 1-indexed, so we add +1
            if has_faces:
                for face in faces:
                    # 'vertex_indices' is the standard name, sometimes it's 'vertex_index'
                    try:
                        indices = face['vertex_indices']
                    except:
                        indices = face['vertex_index']
                        
                    # Write the face line
                    f.write(f"f {indices[0]+1} {indices[1]+1} {indices[2]+1}\n")

        print(f"✅ Success! Surgically saved clean OBJ to: {output_filename}\n")

    except Exception as e:
        print(f"❌ Critical Failure: {e}")

# --- THE LOOP ---
print("🚀 Rhinovate 'Surgical' Extractor Running...")
if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

while True:
    for file in os.listdir(INPUT_FOLDER):
        if file.endswith(".ply"):
            surgical_extract(file)
            try:
                os.rename(os.path.join(INPUT_FOLDER, file), os.path.join(INPUT_FOLDER, file + ".bak"))
            except:
                pass
    time.sleep(2)