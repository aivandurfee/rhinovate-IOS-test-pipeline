import bpy
import os
import glob

# --- CONFIGURATION (DYNAMIC) ---
# This gets the folder where you are currently running the script
BASE_DIR = os.getcwd() 
INPUT_FOLDER = os.path.join(BASE_DIR, "2_Processing")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "3_Outgoing")
# -------------------------------

def run_pipeline():
    # 1. SETUP: Clean the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. AUTO-DETECT: Find the newest OBJ file
    print(f"🔍 Scanning for files in: {INPUT_FOLDER}")
    
    # Get list of all .obj files
    list_of_files = glob.glob(os.path.join(INPUT_FOLDER, '*.obj'))
    
    if not list_of_files:
        print("❌ CRITICAL ERROR: No .obj files found in '2_Processing'.")
        print("   Did the Sanitizer run correctly?")
        return

    # Pick the most recently created file
    latest_file = max(list_of_files, key=os.path.getctime)
    
    # Extract just the filename for naming
    filename_only = os.path.basename(latest_file)
    print(f"📥 Auto-detected newest scan: {filename_only}")

    # 3. IMPORT
    try:
        bpy.ops.wm.obj_import(filepath=latest_file)
    except:
        bpy.ops.import_scene.obj(filepath=latest_file)
        
    obj = bpy.context.selected_objects[0]
    obj.name = "Patient_Scan"

    # 4. MESHING: Turn Dots into Skin (Geometry Nodes)
    print("✨ Meshing Point Cloud...")
    
    mod = obj.modifiers.new(name="Mesher", type='NODES')
    node_group = bpy.data.node_groups.new(name="Meshing_Nodes", type='GeometryNodeTree')
    mod.node_group = node_group
    
    # Define Interface (Blender 4.0+)
    if hasattr(node_group, 'interface'):
        node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = node_group.nodes
    links = node_group.links
    
    # Add Nodes
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    
    pts_to_vol = nodes.new('GeometryNodePointsToVolume')
    # Use 0.05 or 0.06 for sparse scans (iPhone), 0.02 for dense scans (Artec)
    pts_to_vol.inputs['Radius'].default_value = 0.05 
    pts_to_vol.inputs['Voxel Amount'].default_value = 128
    
    vol_to_mesh = nodes.new('GeometryNodeVolumeToMesh')
    vol_to_mesh.inputs['Threshold'].default_value = 0.1
    vol_to_mesh.inputs['Adaptivity'].default_value = 0.1
    
    # Link them
    links.new(input_node.outputs[0], pts_to_vol.inputs[0])
    links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
    # 5. APPLY MODIFIER (Bake to Mesh)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Mesher")
    
    # 6. MORPHING: The "Nose Job"
    print("👃 Applying Healing Morph...")
    
    deform = obj.modifiers.new(name="Rhinoplasty", type='SIMPLE_DEFORM')
    deform.deform_method = 'TAPER'
    deform.factor = 0.5
    
    # 7. EXPORT: Save as GLB using the original filename
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    # Create output name: PLY_Pasha.obj -> PLY_Pasha_healed.glb
    out_name = filename_only.replace(".obj", "_healed.glb")
    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    
    print(f"📤 Exporting to: {out_path}")
    
    bpy.ops.export_scene.gltf(filepath=out_path)
    print("✅ Pipeline Success! Check the output folder.")

if __name__ == "__main__":
    run_pipeline()

# import bpy
# import os

# # --- CONFIGURATION ---
# INPUT_FILE = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\2_Processing\Rhinovate_26-01-16_11-36-56_1768592216498.obj"
# OUTPUT_FOLDER = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\3_Outgoing"
# # ---------------------

# def run_pipeline():
#     # 1. SETUP: Clean the scene
#     bpy.ops.object.select_all(action='SELECT')
#     bpy.ops.object.delete()
    
#     # 2. IMPORT: Load the CLEAN OBJ
#     print(f"📥 Importing Sanitized Mesh: {INPUT_FILE}")
#     if not os.path.exists(INPUT_FILE):
#         print(f"❌ Error: File not found at {INPUT_FILE}")
#         return

#     try:
#         bpy.ops.wm.obj_import(filepath=INPUT_FILE)
#     except:
#         bpy.ops.import_scene.obj(filepath=INPUT_FILE)
        
#     obj = bpy.context.selected_objects[0]
#     obj.name = "Patient_Scan"

#     # 3. MESHING: Turn Dots into Skin (Geometry Nodes)
#     print("✨ Meshing Point Cloud...")
    
#     mod = obj.modifiers.new(name="Mesher", type='NODES')
#     node_group = bpy.data.node_groups.new(name="Meshing_Nodes", type='GeometryNodeTree')
#     mod.node_group = node_group
    
#     # Define Interface (Blender 4.0+)
#     if hasattr(node_group, 'interface'):
#         node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
#         node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

#     nodes = node_group.nodes
#     links = node_group.links
    
#     # Add Nodes
#     input_node = nodes.new('NodeGroupInput')
#     output_node = nodes.new('NodeGroupOutput')
    
#     pts_to_vol = nodes.new('GeometryNodePointsToVolume')
#     pts_to_vol.inputs['Radius'].default_value = 0.06 
#     # pts_to_vol.inputs['Radius'].default_value = 0.025
#     pts_to_vol.inputs['Voxel Amount'].default_value = 128
    
#     vol_to_mesh = nodes.new('GeometryNodeVolumeToMesh')
#     vol_to_mesh.inputs['Threshold'].default_value = 0.1
#     vol_to_mesh.inputs['Adaptivity'].default_value = 0.1
    
#     # Link them
#     links.new(input_node.outputs[0], pts_to_vol.inputs[0])
#     links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
#     links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
#     # 4. APPLY MODIFIER (Bake to Mesh)
#     bpy.context.view_layer.objects.active = obj
#     bpy.ops.object.modifier_apply(modifier="Mesher")
    
#     # 5. MORPHING: The "Nose Job"
#     print("👃 Applying Healing Morph...")
    
#     deform = obj.modifiers.new(name="Rhinoplasty", type='SIMPLE_DEFORM')
#     deform.deform_method = 'TAPER'
#     deform.factor = 0.5
#     # --- FIX: Removed the 'origin' line that caused the crash ---
    
#     # 6. EXPORT: Save as GLB
#     if not os.path.exists(OUTPUT_FOLDER):
#         os.makedirs(OUTPUT_FOLDER)
        
#     out_path = os.path.join(OUTPUT_FOLDER, "healed_result.glb")
#     print(f"📤 Exporting to: {out_path}")
    
#     bpy.ops.export_scene.gltf(filepath=out_path)
#     print("✅ Pipeline Success! Check the output folder.")

# if __name__ == "__main__":
#     run_pipeline()