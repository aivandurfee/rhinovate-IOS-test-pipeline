import bpy
import os

# --- CONFIGURATION ---
# UPDATE THIS PATH to point to your specific .ply file
INPUT_FILE = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\1_Incoming\Rhinovate_26-01-16_11-36-56_1768592216498.ply"
OUTPUT_FOLDER = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\3_Outgoing"
# ---------------------

def run_pipeline():
    # 1. SETUP: Clean the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. IMPORT: Load the raw Point Cloud (PLY)
    print(f"📥 Importing: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        return

    # Blender 4.0+ PLY import
    bpy.ops.wm.ply_import(filepath=INPUT_FILE)
    obj = bpy.context.selected_objects[0]
    obj.name = "Patient_Scan"

    # 3. MESHING: Turn Dots into Skin (Geometry Nodes)
    print("✨ Meshing Point Cloud...")
    
    # Create a new Geometry Node tree
    mod = obj.modifiers.new(name="Mesher", type='NODES')
    node_group = mod.node_group
    
    # Clear default nodes
    for node in node_group.nodes:
        node_group.nodes.remove(node)
        
    # Add Nodes: Points -> Volume -> Mesh
    input_node = node_group.nodes.new('NodeGroupInput')
    output_node = node_group.nodes.new('NodeGroupOutput')
    
    pts_to_vol = node_group.nodes.new('GeometryNodePointsToVolume')
    pts_to_vol.inputs['Radius'].default_value = 0.015  # <--- TWEAK THIS if holes appear (higher = thicker skin)
    pts_to_vol.inputs['Voxel Amount'].default_value = 128 # Resolution
    
    vol_to_mesh = node_group.nodes.new('GeometryNodeVolumeToMesh')
    vol_to_mesh.inputs['Threshold'].default_value = 0.1
    vol_to_mesh.inputs['Adaptivity'].default_value = 0.1 # Optimizes mesh
    
    # Link them
    node_group.links.new(input_node.outputs[0], pts_to_vol.inputs[0])
    node_group.links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    node_group.links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
    # Apply the modifier to make it real geometry
    bpy.ops.object.modifier_apply(modifier="Mesher")
    
    # 4. MORPHING: The "Nose Job" (Simple Taper)
    print("👃 Applying Healing Morph...")
    
    # Add a deform modifier (Mocking the AI morph for now)
    deform = obj.modifiers.new(name="Rhinoplasty", type='SIMPLE_DEFORM')
    deform.deform_method = 'TAPER'
    deform.factor = 0.5  # Positive = pinch, Negative = expand
    deform.origin = obj  # Taper around center
    
    # 5. EXPORT: Save as GLB (Mobile Ready)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    out_path = os.path.join(OUTPUT_FOLDER, "healed_result.glb")
    print(f"📤 Exporting to: {out_path}")
    
    bpy.ops.export_scene.gltf(filepath=out_path)
    print("✅ Pipeline Success! Check the output folder.")

if __name__ == "__main__":
    run_pipeline()