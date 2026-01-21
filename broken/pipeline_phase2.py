import bpy
import os

# --- CONFIGURATION ---
# We look in "2_Processing" because that is where the Sanitizer saved the clean file
INPUT_FILE = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\2_Processing\Rhinovate_26-01-16_11-36-56_1768592216498.obj"
OUTPUT_FOLDER = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\3_Outgoing"
# ---------------------

def run_pipeline():
    # 1. SETUP: Clean the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. IMPORT: Load the CLEAN OBJ (The one Trimesh fixed)
    print(f"📥 Importing Sanitized Mesh: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        print("   Did you run 'sanitize_trimesh.py' first?")
        return

    # Use the standard OBJ importer
    # Note: If this fails on specific Blender versions, try bpy.ops.import_scene.obj()
    try:
        bpy.ops.wm.obj_import(filepath=INPUT_FILE)
    except:
        bpy.ops.import_scene.obj(filepath=INPUT_FILE)
        
    obj = bpy.context.selected_objects[0]
    obj.name = "Patient_Scan"

    # 3. MESHING: Turn Dots into Skin (Geometry Nodes)
    # Even though it's an OBJ now, it's likely still just floating vertices (dots).
    # We need to wrap a skin around them.
    print("✨ Meshing Point Cloud...")
    
    mod = obj.modifiers.new(name="Mesher", type='NODES')
    node_group = mod.node_group
    
    # Clear default nodes
    for node in node_group.nodes:
        node_group.nodes.remove(node)
        
    # Add Nodes: Points -> Volume -> Mesh
    input_node = node_group.nodes.new('NodeGroupInput')
    output_node = node_group.nodes.new('NodeGroupOutput')
    
    pts_to_vol = node_group.nodes.new('GeometryNodePointsToVolume')
    pts_to_vol.inputs['Radius'].default_value = 0.015  # Thickness of the skin
    pts_to_vol.inputs['Voxel Amount'].default_value = 128 # Resolution
    
    vol_to_mesh = node_group.nodes.new('GeometryNodeVolumeToMesh')
    vol_to_mesh.inputs['Threshold'].default_value = 0.1
    vol_to_mesh.inputs['Adaptivity'].default_value = 0.1
    
    # Link them
    node_group.links.new(input_node.outputs[0], pts_to_vol.inputs[0])
    node_group.links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    node_group.links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
    # Bake the mesh (Make it real geometry)
    bpy.ops.object.modifier_apply(modifier="Mesher")
    
    # 4. MORPHING: The "Nose Job"
    print("👃 Applying Healing Morph...")
    
    deform = obj.modifiers.new(name="Rhinoplasty", type='SIMPLE_DEFORM')
    deform.deform_method = 'TAPER'
    deform.factor = 0.5
    deform.origin = obj
    
    # 5. EXPORT: Save as GLB
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    out_path = os.path.join(OUTPUT_FOLDER, "healed_result.glb")
    print(f"📤 Exporting to: {out_path}")
    
    bpy.ops.export_scene.gltf(filepath=out_path)
    print("✅ Pipeline Success! Check the output folder.")

if __name__ == "__main__":
    run_pipeline()