# import trimesh
# import os
# import time

# # ---------------- CONFIGURATION ----------------
# INPUT_FOLDER = "1_Incoming"
# OUTPUT_FOLDER = "2_Processing"
# # -----------------------------------------------

# def force_load_trimesh(filename):
#     print(f"👀 Detecting new scan: {filename}")
#     input_path = os.path.join(INPUT_FOLDER, filename)
#     output_filename = filename.replace(".ply", ".obj")
#     output_path = os.path.join(OUTPUT_FOLDER, output_filename)

#     try:
#         # 1. LOAD AS SCENE (The Secret Trick)
#         # Instead of trimesh.load(..., force='mesh'), we load as a 'Scene'.
#         # Scenes are much better at handling broken pieces.
#         scene = trimesh.load(input_path, force='scene')
        
#         # 2. DUMP GEOMETRY
#         # A scene might have multiple pieces. We grab the first geometry we find.
#         # This bypasses the "Face Color" check because we aren't validating a single mesh yet.
        
#         if len(scene.geometry) == 0:
#             print("❌ No geometry found in scene.")
#             return

#         # Grab the first mesh in the dictionary
#         mesh_name = list(scene.geometry.keys())[0]
#         mesh = scene.geometry[mesh_name]
        
#         print(f"   Found geometry: {len(mesh.vertices)} verts")

#         # 3. STRIP BROKEN COLORS
#         # We manually delete the color data that is causing the crash
#         mesh.visual = trimesh.visual.ColorVisuals(mesh) # Reset to blank
        
#         # 4. EXPORT
#         mesh.export(output_path)
#         print(f"✅ Success! Cleaned and saved to: {output_filename}\n")

#     except Exception as e:
#         print(f"❌ Standard load failed: {e}")
#         print("   Attempting raw binary load...")
        
#         # FALLBACK: If Trimesh refuses to load it, it's really broken.
#         # But usually 'force="scene"' fixes the color shape error.

# # --- THE LOOP ---
# print("🚀 Rhinovate 'Trimesh-Force' Running...")
# if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
# if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

# while True:
#     for file in os.listdir(INPUT_FOLDER):
#         if file.endswith(".ply"):
#             force_load_trimesh(file)
#             try:
#                 os.rename(os.path.join(INPUT_FOLDER, file), os.path.join(INPUT_FOLDER, file + ".bak"))
#             except:
#                 pass
#     time.sleep(2)


import trimesh
import os
import sys

# ---------------- CONFIGURATION ----------------
INPUT_FOLDER = "1_Incoming"
OUTPUT_FOLDER = "2_Processing"
# -----------------------------------------------

def force_load_trimesh(filename):
    print(f"👀 Detecting scan: {filename}")
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_filename = filename.replace(".ply", ".obj")
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    try:
        # 1. LOAD AS SCENE (The Secret Trick)
        scene = trimesh.load(input_path, force='scene')
        
        # 2. DUMP GEOMETRY
        if len(scene.geometry) == 0:
            print("❌ No geometry found in scene.")
            return

        # Grab the first mesh in the dictionary
        mesh_name = list(scene.geometry.keys())[0]
        mesh = scene.geometry[mesh_name]
        
        print(f"   Found geometry: {len(mesh.vertices)} verts")

        # 3. STRIP BROKEN COLORS & EXPORT
        mesh.visual = trimesh.visual.ColorVisuals(mesh) # Reset to blank
        mesh.export(output_path)
        print(f"✅ Success! Cleaned and saved to: {output_filename}\n")

    except Exception as e:
        print(f"❌ Standard load failed: {e}")

# --- MAIN EXECUTION (NO LOOP) ---
if __name__ == "__main__":
    print("🚀 Rhinovate Sanitizer Running (One-Pass)...")
    
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

    files_found = False
    
    # Process all PLY files currently in the folder
    for file in os.listdir(INPUT_FOLDER):
        if file.endswith(".ply"):
            files_found = True
            force_load_trimesh(file)
            # Optional: Rename to .bak if you want to keep track of what is done
            # os.rename(os.path.join(INPUT_FOLDER, file), os.path.join(INPUT_FOLDER, file + ".bak"))
    
    if not files_found:
        print("⚠️  No .ply files found in '1_Incoming'. (Did you forget to remove the .bak extension?)")
        
    print("🏁 Sanitizer Finished.")