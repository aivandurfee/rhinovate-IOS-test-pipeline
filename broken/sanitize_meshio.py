import meshio
import os
import time

# ---------------- CONFIGURATION ----------------
INPUT_FOLDER = "1_Incoming"
OUTPUT_FOLDER = "2_Processing"
# -----------------------------------------------

def force_convert(filename):
    print(f"👀 Detecting new scan: {filename}")
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_filename = filename.replace(".ply", ".obj")
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    try:
        # 1. Read with Meshio (The "Forgiving" Reader)
        # It separates data into blocks, so it won't crash if one block is weird
        mesh = meshio.read(input_path)
        
        print(f"   Stats: {len(mesh.points)} points, {len(mesh.cells_dict.get('triangle', []))} triangles")

        # 2. PRUNE the bad data
        # We create a NEW mesh with ONLY the geometry (Points + Triangles)
        # We explicitly drop the 'point_data' and 'cell_data' (colors) which are corrupted
        clean_mesh = meshio.Mesh(
            points=mesh.points,
            cells={"triangle": mesh.cells_dict["triangle"]}
        )

        # 3. Save as OBJ
        clean_mesh.write(output_path)
        print(f"✅ Success! Saved clean geometry to: {output_filename}\n")

    except Exception as e:
        print(f"❌ Failed: {e}")
        # If even Meshio fails, the file is likely empty or 0kb.

# --- THE LOOP ---
print("🚀 Rhinovate 'Nuclear' Fixer Running...")
if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

while True:
    for file in os.listdir(INPUT_FOLDER):
        if file.endswith(".ply"):
            force_convert(file)
            try:
                os.rename(os.path.join(INPUT_FOLDER, file), os.path.join(INPUT_FOLDER, file + ".bak"))
            except:
                pass
    time.sleep(2)