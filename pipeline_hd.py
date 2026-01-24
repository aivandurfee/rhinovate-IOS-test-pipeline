"""
Rhinovate Blender morph engine: OBJ → morphed GLB.
Loads sanitized OBJ from 2_Processing, optionally voxelizes (Points→Volume→Mesh),
applies lattice-based nose morph, exports to 3_Outgoing. Uses config.json via
RHINOVATE_PROJECT_ROOT. Run via: blender --background --python pipeline_hd.py
"""
from __future__ import annotations

import json
import os
import sys
import glob

import bpy
import mathutils

CONFIG_NAME = "config.json"


def _load_config() -> dict:
    root = os.environ.get("RHINOVATE_PROJECT_ROOT")
    if not root or not os.path.isdir(root):
        root = os.getcwd()
    path = os.path.join(root, CONFIG_NAME)
    if not os.path.isfile(path):
        print(f"[FAIL] Config not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fail(msg: str) -> None:
    print(msg)
    sys.exit(1)


def _voxelize(obj: bpy.types.Object, cfg: dict) -> None:
    """Points→Volume→Mesh. Use Mesh to Points if input is mesh (e.g. vertices-only OBJ)."""
    mod = obj.modifiers.new(name="Mesher", type="NODES")
    ng = bpy.data.node_groups.new(name="Meshing_Nodes", type="GeometryNodeTree")
    mod.node_group = ng

    if hasattr(ng, "interface"):
        ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links
    inp = nodes.new("NodeGroupInput")
    out = nodes.new("NodeGroupOutput")

    mesh_to_pts = nodes.new("GeometryNodeMeshToPoints")
    mesh_to_pts.mode = "VERTICES"

    pts_to_vol = nodes.new("GeometryNodePointsToVolume")
    pts_to_vol.inputs["Radius"].default_value = float(cfg.get("voxel_radius", 0.05))
    pts_to_vol.inputs["Voxel Amount"].default_value = int(cfg.get("voxel_amount", 128))

    vol_to_mesh = nodes.new("GeometryNodeVolumeToMesh")
    vol_to_mesh.inputs["Threshold"].default_value = float(cfg.get("volume_threshold", 0.1))
    vol_to_mesh.inputs["Adaptivity"].default_value = float(cfg.get("volume_adaptivity", 0.1))

    links.new(inp.outputs[0], mesh_to_pts.inputs[0])
    links.new(mesh_to_pts.outputs[0], pts_to_vol.inputs[0])
    links.new(pts_to_vol.outputs[0], vol_to_mesh.inputs[0])
    links.new(vol_to_mesh.outputs[0], out.inputs[0])

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Mesher")


def _ensure_visible(obj: bpy.types.Object) -> None:
    """Ensure mesh is centered at origin and has valid geometry."""
    # Update mesh data
    obj.update_from_editmode()
    obj.data.update()
    
    # Get dimensions
    dims = obj.dimensions
    print(f"   Mesh dimensions: {dims}")
    print(f"   Vertices: {len(obj.data.vertices)}")
    
    # Check if mesh has geometry
    if len(obj.data.vertices) == 0:
        print("[WARN] Mesh has no vertices after processing!")
        return
    
    # Ensure origin is at geometry center
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    
    # Move to world origin
    obj.location = (0, 0, 0)
    
    # Frame the view (useful for debugging, but we're in headless mode)
    # bpy.ops.view3d.view_all()


def _lattice_morph(obj: bpy.types.Object, cfg: dict) -> None:
    """9×9×9 lattice around bbox center, resize middle U-columns on X."""
    lp = int(cfg.get("lattice_points", 9))
    pad = float(cfg.get("lattice_padding", 1.1))
    resize_x = float(cfg.get("lattice_resize_x", 0.8))
    brush = float(cfg.get("lattice_brush_factor", 0.25))

    local_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
    global_center = obj.matrix_world @ local_center
    dims = obj.dimensions

    lat_data = bpy.data.lattices.new("Nose_Cage")
    lat_obj = bpy.data.objects.new("Nose_Cage", lat_data)
    bpy.context.collection.objects.link(lat_obj)

    lat_data.points_u = lat_data.points_v = lat_data.points_w = lp
    lat_obj.location = global_center
    lat_obj.scale = (dims.x * pad, dims.y * pad, dims.z * pad)

    mod = obj.modifiers.new(name="Lattice_Deform", type="LATTICE")
    mod.object = lat_obj

    mid = lp // 2
    for i, pt in enumerate(lat_data.points):
        if (i % lp) in (mid - 1, mid, mid + 1):
            pt.select = True
        else:
            pt.select = False

    bpy.context.view_layer.objects.active = lat_obj
    bpy.ops.object.mode_set(mode="EDIT")
    brush_size = dims.x * brush
    bpy.ops.transform.resize(
        value=(resize_x, 1.0, 1.0),
        use_proportional_edit=True,
        proportional_edit_falloff="SMOOTH",
        proportional_size=brush_size,
    )
    bpy.ops.object.mode_set(mode="OBJECT")


def run_pipeline() -> None:
    config = _load_config()
    folders = config.get("folders", {})
    proc = folders.get("processing", "2_Processing")
    out = folders.get("outgoing", "3_Outgoing")

    root = os.environ.get("RHINOVATE_PROJECT_ROOT", os.getcwd())
    input_dir = os.path.join(root, proc)
    output_dir = os.path.join(root, out)
    os.makedirs(output_dir, exist_ok=True)

    obj_files = glob.glob(os.path.join(input_dir, "*.obj"))
    if not obj_files:
        _fail("[FAIL] No .obj files in '2_Processing'. Run sanitizer first.")

    latest = max(obj_files, key=os.path.getctime)
    filename = os.path.basename(latest)
    print(f"Loading: {filename}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    try:
        bpy.ops.wm.obj_import(filepath=latest)
    except Exception:
        try:
            bpy.ops.import_scene.obj(filepath=latest)
        except Exception as e:
            _fail(f"[FAIL] Import failed: {e}")

    objs_sel = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    if not objs_sel:
        _fail("[FAIL] No mesh imported.")
    obj = objs_sel[0]
    obj.name = "Patient_Scan"
    bpy.ops.object.shade_smooth()
    
    print(f"   Initial vertices: {len(obj.data.vertices)}")

    pl = config.get("pipeline", {})
    if pl.get("use_voxelization"):
        print("Voxelizing...")
        _voxelize(obj, pl)
        _ensure_visible(obj)

    print("Applying lattice morph...")
    _lattice_morph(obj, pl)
    _ensure_visible(obj)

    out_name = filename.replace(".obj", "_healed.glb")
    out_path = os.path.join(output_dir, out_name)
    
    # Final validation
    if len(obj.data.vertices) == 0:
        _fail("[FAIL] Mesh has no vertices - cannot export!")
    
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    
    # Export with proper settings
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        use_selection=True,
        export_apply=True,
        export_format="GLB",
    )
    print(f"[OK] Exported: {out_name} ({len(obj.data.vertices)} vertices, dims: {obj.dimensions})")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"[FAIL] Pipeline error: {e}")
        sys.exit(1)
