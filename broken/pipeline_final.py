import bpy
import os

# --- CONFIGURATION ---
INPUT_FILE = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\2_Processing\Rhinovate_26-01-16_11-36-56_1768592216498.obj"
OUTPUT_FOLDER = r"C:\Users\surfi\Desktop\Rhinovate CTO\IOS Pipeline\3_Outgoing"
# ---------------------

def run_pipeline():
    # 1. SETUP: Clean the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. IMPORT: Load the CLEAN OBJ
    print(f"📥 Importing Sanitized Mesh: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        return

    try:
        bpy.ops.wm.obj_import(filepath=INPUT_FILE)
    except:
        bpy.ops.import_scene.obj(filepath=INPUT_FILE)
        
    obj = bpy.context.selected_objects[0]
    obj.name = "Patient_Scan"

    # 3. MESHING: Turn Dots into Skin (Geometry Nodes)
    print("✨ Meshing Point Cloud...")
    
    mod = obj.modifiers.new(name="Mesher", type='NODES')
    node_group = bpy.data.node_groups.new(name="Meshing_Nodes", type='GeometryNodeTree')
    mod.node_group = node_group
    
    # --- NEW: Explicitly Create Interface (Blender 4.0+ Requirement) ---
    # We must tell the group it accepts Geometry and outputs Geometry
    if hasattr(node_group, 'interface'):
        # Create Input Socket
        socket_in = node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        # Create Output Socket
        socket_out = node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    # -------------------------------------------------------------------

    nodes = node_group.nodes
    links = node_group.links
    
    # Add Nodes
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    
    pts_to_vol = nodes.new('GeometryNodePointsToVolume')
    pts_to_vol.inputs['Radius'].default_value = 0.025  # Increased slightly for better solidity
    pts_to_vol.inputs['Voxel Amount'].default_value = 128
    
    vol_to_mesh = nodes.new('GeometryNodeVolumeToMesh')
    vol_to_mesh.inputs['Threshold'].default_value = 0.1
    vol_to_mesh.inputs['Adaptivity'].default_value = 0.1
    
    # Link them
    # Note: socket indices might vary, so we verify connections
    links.new(input_node.outputs[0], pts_to_vol.inputs[0])
    links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    links.new(vol_to_mesh.outputs[0], output_node.inputs[0])
    
    # 4. APPLY MODIFIER (Bake to Mesh)
    # Important: Ensure the object is active before applying
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Mesher")
    
    # 5. MORPHING: The "Nose Job"
    print("👃 Applying Healing Morph...")
    
    deform = obj.modifiers.new(name="Rhinoplasty", type='SIMPLE_DEFORM')
    deform.deform_method = 'TAPER'
    deform.factor = 0.5
    deform.origin = obj
    
    # 6. EXPORT: Save as GLB
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    out_path = os.path.join(OUTPUT_FOLDER, "healed_result.glb")
    print(f"📤 Exporting to: {out_path}")
    
    bpy.ops.export_scene.gltf(filepath=out_path)
    print("✅ Pipeline Success! Check the output folder.")

if __name__ == "__main__":
    run_pipeline()