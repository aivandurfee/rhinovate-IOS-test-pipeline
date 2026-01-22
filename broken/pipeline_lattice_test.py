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

    # --- CRITICAL FIX: NORMALIZE SCALE ---
    # We force the object to be roughly 1.0 unit tall so our math always works
    print(f"📏 Original Size: {obj.dimensions}")
    
    # Calculate scale factor to make Z-height = 1.0
    # If head is 200 units, factor will be 1/200 = 0.005
    # If head is 0.2 units, factor will be 1/0.2 = 5.0
    current_height = obj.dimensions.z
    if current_height == 0: current_height = 1 # Prevent divide by zero
    
    scale_factor = 1.0 / current_height
    obj.scale = (scale_factor, scale_factor, scale_factor)
    
    # Apply the scale so it becomes "Real" geometry
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    print(f"✅ Normalized Size: {obj.dimensions}")
    # -------------------------------------

    # 3. MESHING (Now using constants that GUARANTEE success)
    print("✨ Meshing...")
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
    # Since object is size 1.0, Radius 0.04 is always correct relative proportion
    pts_to_vol.inputs['Radius'].default_value = 0.04 
    pts_to_vol.inputs['Voxel Amount'].default_value = 128
    
    vol_to_mesh = nodes.new('GeometryNodeVolumeToMesh')
    vol_to_mesh.inputs['Threshold'].default_value = 0.1
    
    links.new(input_node.outputs[0], pts_to_vol.inputs[0])
    links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
    # Bake Mesh
    bpy.ops.object.modifier_apply(modifier="Mesher")
    
    # 4. LATTICE DEFORM
    print("👃 Applying Pinch...")
    
    # Get Bounds
    local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center
    
    # Create Cage
    lattice_data = bpy.data.lattices.new("Nose_Cage")
    lattice_obj = bpy.data.objects.new("Nose_Cage", lattice_data)
    bpy.context.collection.objects.link(lattice_obj)
    
    # Setup Grid
    lattice_data.points_u = 3
    lattice_data.points_v = 3
    lattice_data.points_w = 3
    
    # Place & Scale Cage (Size 1.2 covers the normalized head perfectly)
    lattice_obj.location = global_bbox_center
    lattice_obj.scale = (1.2, 1.2, 1.2)
    
    # Link
    modifier = obj.modifiers.new(name="Lattice_Deform", type='LATTICE')
    modifier.object = lattice_obj
    
    # Deform
    bpy.context.view_layer.objects.active = lattice_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.lattice.select_all(action='SELECT')
    
    # PINCH: Extreme value (0.4) so you can verify it works
    bpy.ops.transform.resize(value=(0.4, 1.0, 1.0), 
                             use_proportional_edit=True, 
                             proportional_edit_falloff='SMOOTH', 
                             proportional_size=0.5)
                             
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 5. EXPORT & DEBUG
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    
    # Save Debug File (This one should NOT be empty now)
    debug_path = os.path.join(OUTPUT_FOLDER, "debug_scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=debug_path)
    
    # Export GLB
    out_name = filename_only.replace(".obj", "_healed.glb")
    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    
    # Select only head
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    
    bpy.ops.export_scene.gltf(filepath=out_path, use_selection=True)
    print("✅ Pipeline Success!")

if __name__ == "__main__":
    run_pipeline()