# import open3d as o3d
# import os
# import time

# # ---------------- CONFIGURATION ----------------
# INPUT_FOLDER = "1_Incoming"
# OUTPUT_FOLDER = "2_Processing"
# # -----------------------------------------------

# def convert_ply_to_obj(filename):
#     print(f"👀 Detecting new scan: {filename}")
    
#     # 1. Load the PLY (Point Cloud or Mesh)
#     input_path = os.path.join(INPUT_FOLDER, filename)
#     mesh = o3d.io.read_triangle_mesh(input_path)
    
#     # Check if it loaded correctly
#     if not mesh.has_triangles():
#         print("⚠️  Warning: File is a Point Cloud (dots), not a Mesh.")
#         print("   Attempting to generate a mesh surface...")
#         # (Simple Ball Pivoting or Poisson could go here, but let's try reading as point cloud first)
#         pcd = o3d.io.read_point_cloud(input_path)
#         # Estimate normals if they don't exist
#         pcd.estimate_normals()
#         # Create a mesh using Poisson reconstruction (Standard "Shrink Wrap" method)
#         mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)

#     # 2. Optimize (Clean up the scan)
#     # Remove weird floating artifacts common in LiDAR
#     mesh.remove_degenerate_triangles()
#     mesh.remove_duplicated_triangles()
#     mesh.remove_duplicated_vertices()
#     mesh.remove_non_manifold_edges()
    
#     # 3. Save as OBJ (The format Blender needs)
#     output_filename = filename.replace(".ply", ".obj")
#     output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
#     o3d.io.write_triangle_mesh(output_path, mesh)
#     print(f"✅ Success! Converted to: {output_filename}\n")

# # --- THE "WATCHDOG" LOOP ---
# print("🚀 Rhinovate Ingest Server Running...")
# print(f"   Waiting for PLY files in /{INPUT_FOLDER}...")

# while True:
#     # Look for files in the incoming folder
#     for file in os.listdir(INPUT_FOLDER):
#         if file.endswith(".ply"):
#             convert_ply_to_obj(file)
#             # Move original file to 'processed' folder or delete it so we don't re-convert
#             # For now, let's just rename it to .bak
#             os.rename(os.path.join(INPUT_FOLDER, file), os.path.join(INPUT_FOLDER, file + ".bak"))
    
#     time.sleep(2) # Check every 2 seconds