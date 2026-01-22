# import bpy
# import os
# import glob
# import mathutils
# import math

# # --- CONFIGURATION ---
# BASE_DIR = os.getcwd() 
# INPUT_FOLDER = os.path.join(BASE_DIR, "2_Processing")
# OUTPUT_FOLDER = os.path.join(BASE_DIR, "3_Outgoing")
# # ---------------------

# def run_pipeline():
#     # 1. SETUP
#     print("🧹 Clearing Scene...")
#     bpy.ops.object.select_all(action='SELECT')
#     bpy.ops.object.delete()
    
#     # 2. AUTO-DETECT
#     list_of_files = glob.glob(os.path.join(INPUT_FOLDER, '*.obj'))
#     if not list_of_files: 
#         print("❌ No files found.")
#         return

#     latest_file = max(list_of_files, key=os.path.getctime)
#     filename_only = os.path.basename(latest_file)
#     print(f"📥 Loading: {filename_only}")

#     try:
#         bpy.ops.wm.obj_import(filepath=latest_file)
#     except:
#         bpy.ops.import_scene.obj(filepath=latest_file)
        
#     obj = bpy.context.selected_objects[0]
#     obj.name = "Patient_Scan"
    
#     # FORCE SMOOTH SHADING (Fixes the faceted look without destroying data)
#     bpy.ops.object.shade_smooth()

#     # 3. SMART LATTICE SETUP (No Object Scaling!)
#     print("📏 Measuring Patient...")
    
#     # Calculate the exact center of the geometry (not just the origin point)
#     local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
#     global_bbox_center = obj.matrix_world @ local_bbox_center
    
#     # Calculate the size of the geometry
#     dimensions = obj.dimensions
#     print(f"   Center: {global_bbox_center}")
#     print(f"   Size: {dimensions}")

#     # Create the Cage
#     lattice_data = bpy.data.lattices.new("Nose_Cage")
#     lattice_obj = bpy.data.objects.new("Nose_Cage", lattice_data)
#     bpy.context.collection.objects.link(lattice_obj)
    
#     # 3x3x3 Grid (Center point controls the nose)
#     lattice_data.points_u = 3
#     lattice_data.points_v = 3
#     lattice_data.points_w = 3
    
#     # ALIGNMENT: Place the cage exactly on the face center
#     lattice_obj.location = global_bbox_center
    
#     # SCALING: Size the cage to fit this specific patient (with 20% padding)
#     # This replaces the need to resize the patient!
#     lattice_obj.scale = (dimensions.x * 1.2, dimensions.y * 1.2, dimensions.z * 1.2)
    
#     # Link Modifier
#     modifier = obj.modifiers.new(name="Lattice_Deform", type='LATTICE')
#     modifier.object = lattice_obj
    
#     # 4. SURGICAL MORPH
#     print("👃 Applying Correction...")
#     bpy.context.view_layer.objects.active = lattice_obj
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.lattice.select_all(action='DESELECT')
    
#     # SELECT CENTER POINTS (The Nose Area)
#     # We select points inside the middle 30% of the box
#     bpy.ops.lattice.select_all(action='SELECT')
    
#     # DYNAMIC CALCULATIONS
#     # We need to tune the 'Proportional Size' to the patient's actual size.
#     # For a head 200mm wide, a 150mm brush (0.75 factor) grabs the cheeks.
#     # A 40mm brush (0.2 factor) grabs just the nose.
#     brush_radius = dimensions.x * 0.2
    
#     # THE PINCH:
#     # Resize X axis to 85% (Thinning)
#     bpy.ops.transform.resize(value=(0.85, 1.0, 1.0), 
#                              use_proportional_edit=True, 
#                              proportional_edit_falloff='SMOOTH', 
#                              proportional_size=brush_radius)
                             
#     bpy.ops.object.mode_set(mode='OBJECT')
    
#     # 5. EXPORT
#     if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
#     # Save Debug File (To verify alignment)
#     debug_path = os.path.join(OUTPUT_FOLDER, "debug_scene.blend")
#     bpy.ops.wm.save_as_mainfile(filepath=debug_path)
    
#     # Export GLB
#     out_name = filename_only.replace(".obj", "_healed.glb")
#     out_path = os.path.join(OUTPUT_FOLDER, out_name)
    
#     # Ensure we only export the mesh, not the lattice box
#     bpy.ops.object.select_all(action='DESELECT')
#     obj.select_set(True)
    
#     # Export with "Apply Modifiers" to bake the pinch
#     bpy.ops.export_scene.gltf(filepath=out_path, use_selection=True, export_apply=True)
#     print("✅ Pipeline Success!")

# if __name__ == "__main__":
#     run_pipeline()


import bpy
import os
import glob
import mathutils

# --- CONFIGURATION ---
BASE_DIR = os.getcwd() 
INPUT_FOLDER = os.path.join(BASE_DIR, "2_Processing")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "3_Outgoing")
# ---------------------

def run_pipeline():
    # 1. SETUP
    print("🧹 Clearing Scene...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. AUTO-DETECT
    list_of_files = glob.glob(os.path.join(INPUT_FOLDER, '*.obj'))
    if not list_of_files: 
        print("❌ No files found.")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    filename_only = os.path.basename(latest_file)
    print(f"📥 Loading: {filename_only}")

    try:
        bpy.ops.wm.obj_import(filepath=latest_file)
    except:
        bpy.ops.import_scene.obj(filepath=latest_file)
        
    obj = bpy.context.selected_objects[0]
    obj.name = "Patient_Scan"
    bpy.ops.object.shade_smooth()

    # 3. ALIGNMENT
    print("📏 Measuring Patient...")
    local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center
    dimensions = obj.dimensions

    # 4. HIGH-RES LATTICE SETUP (9x9x9)
    lattice_data = bpy.data.lattices.new("Nose_Cage")
    lattice_obj = bpy.data.objects.new("Nose_Cage", lattice_data)
    bpy.context.collection.objects.link(lattice_obj)
    
    # 9 points wide means indices 0,1,2 (Left Ear), 3,4,5 (Nose), 6,7,8 (Right Ear)
    lattice_data.points_u = 9  
    lattice_data.points_v = 9
    lattice_data.points_w = 9
    
    # Place & Scale Cage (10% padding ensures we capture chin and forehead)
    lattice_obj.location = global_bbox_center
    lattice_obj.scale = (dimensions.x * 1.1, dimensions.y * 1.1, dimensions.z * 1.1)
    
    modifier = obj.modifiers.new(name="Lattice_Deform", type='LATTICE')
    modifier.object = lattice_obj
    
    # 5. SURGICAL SELECTION (The Math Fix)
    print("👃 Selecting Nose Area...")
    
    # Instead of entering Edit Mode to select (which is tricky in headless),
    # We select the points directly in the data block.
    
    # Reset all selection
    for point in lattice_data.points:
        point.select = False
        
    # Select ONLY the middle columns (Indices 3, 4, 5)
    # The points are stored in a flat list, but we know the U-dimension is 9.
    # U-Index = index % points_u
    u_points = lattice_data.points_u
    
    for i, point in enumerate(lattice_data.points):
        u_index = i % u_points
        
        # If the point is in the middle 3 columns...
        if u_index in [3, 4, 5]:
            point.select = True
            
    # 6. APPLY THE PINCH
    bpy.context.view_layer.objects.active = lattice_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Tune the brush size to be the width of the nose bridge only
    brush_radius = dimensions.x * 0.25
    
    # Resize X-Axis to 85% (Thinning)
    bpy.ops.transform.resize(value=(0.80, 1.0, 1.0), 
                             use_proportional_edit=True, 
                             proportional_edit_falloff='SMOOTH', 
                             proportional_size=brush_radius)
                             
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 7. EXPORT
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
    out_name = filename_only.replace(".obj", "_healed.glb")
    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    
    # Export using 'Apply Modifiers' so the GLB has the shape baked in
    bpy.ops.export_scene.gltf(filepath=out_path, use_selection=True, export_apply=True)
    print("✅ Pipeline Success!")

if __name__ == "__main__":
    run_pipeline()