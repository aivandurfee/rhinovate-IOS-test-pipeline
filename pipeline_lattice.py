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

    # --- NORMALIZE SCALE ---
    print(f"📏 Original Size: {obj.dimensions}")
    current_height = obj.dimensions.z
    if current_height == 0: current_height = 1
    
    normalize_factor = 1.0 / current_height
    obj.scale = (normalize_factor, normalize_factor, normalize_factor)
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # -----------------------

    # 3. MESHING (HIGH RES + SMOOTHING)
    print("✨ Meshing & Polishing...")
    mod = obj.modifiers.new(name="Mesher", type='NODES')
    node_group = bpy.data.node_groups.new(name="Meshing_Nodes", type='GeometryNodeTree')
    mod.node_group = node_group
    
    if hasattr(node_group, 'interface'):
        node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = node_group.nodes
    links = node_group.links
    
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    
    pts_to_vol = nodes.new('GeometryNodePointsToVolume')
    # High Res Settings
    pts_to_vol.inputs['Radius'].default_value = 0.015 
    pts_to_vol.inputs['Voxel Amount'].default_value = 512
    
    vol_to_mesh = nodes.new('GeometryNodeVolumeToMesh')
    vol_to_mesh.inputs['Threshold'].default_value = 0.1
    vol_to_mesh.inputs['Adaptivity'].default_value = 0.0 # Keep all details
    
    links.new(input_node.outputs[0], pts_to_vol.inputs[0])
    links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
    bpy.ops.object.modifier_apply(modifier="Mesher")

    # --- NEW STEP: THE "SANDPAPER" ---
    # This melts the "Topography Steps" into smooth skin
    smooth_mod = obj.modifiers.new(name="Polisher", type='CORRECTIVE_SMOOTH')
    smooth_mod.iterations = 25       # Run the sanding 25 times
    smooth_mod.smooth_type = 'LENGTH_WEIGHTED'
    smooth_mod.factor = 0.8          # Strong smoothing strength
    
    bpy.ops.object.modifier_apply(modifier="Polisher")
    
    # Force "Shade Smooth" visual (removes faceting)
    bpy.ops.object.shade_smooth()
    # ---------------------------------
    
    # 4. SURGICAL MORPH (PRECISION UPDATE)
    print("👃 Applying Precision Correction...")
    
    local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center
    
    lattice_data = bpy.data.lattices.new("Nose_Cage")
    lattice_obj = bpy.data.objects.new("Nose_Cage", lattice_data)
    bpy.context.collection.objects.link(lattice_obj)
    
    lattice_data.points_u = 3
    lattice_data.points_v = 3
    lattice_data.points_w = 3
    
    lattice_obj.location = global_bbox_center
    lattice_obj.scale = (1.2, 1.2, 1.2)
    
    modifier = obj.modifiers.new(name="Lattice_Deform", type='LATTICE')
    modifier.object = lattice_obj
    
    bpy.context.view_layer.objects.active = lattice_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.lattice.select_all(action='SELECT')
    
    # --- PRECISION FIX ---
    # proportional_size was 0.5 (Huge). We changed it to 0.15
    # This ensures we ONLY grab the nose, not the cheeks.
    bpy.ops.transform.resize(value=(0.85, 1.0, 1.0), 
                             use_proportional_edit=True, 
                             proportional_edit_falloff='SMOOTH', 
                             proportional_size=0.15) 
                             
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Lattice_Deform")
    bpy.data.objects.remove(lattice_obj, do_unlink=True)

    # --- RE-INFLATE ---
    print(f"🔄 Restoring Original Scale...")
    restore_factor = 1.0 / normalize_factor
    obj.scale = (restore_factor, restore_factor, restore_factor)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # 5. EXPORT
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
    out_name = filename_only.replace(".obj", "_healed.glb")
    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    
    bpy.ops.export_scene.gltf(filepath=out_path, use_selection=True)
    print("✅ Pipeline Success!")

if __name__ == "__main__":
    run_pipeline()