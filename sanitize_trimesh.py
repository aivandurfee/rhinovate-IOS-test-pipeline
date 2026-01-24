"""
Rhinovate sanitizer: PLY → cleaned OBJ.
Loads iOS LiDAR PLY, repairs bad vertex indices / degenerate geometry, strips broken
colors, exports to OBJ for the Blender pipeline. Uses config.json via RHINOVATE_PROJECT_ROOT.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import trimesh

CONFIG_NAME = "config.json"


def _load_config() -> dict:
    root = os.environ.get("RHINOVATE_PROJECT_ROOT")
    if not root or not os.path.isdir(root):
        root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, CONFIG_NAME)
    if not os.path.isfile(path):
        print(f"[FAIL] Config not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _filter_noise(mesh, config: dict) -> trimesh.PointCloud | trimesh.Trimesh:
    """Filter noise from point cloud to isolate dense face region.
    Returns a new mesh/pointcloud with outliers removed.
    """
    if not isinstance(mesh, trimesh.PointCloud):
        # If it's already a mesh, convert to point cloud for filtering
        if hasattr(mesh, "vertices"):
            mesh = trimesh.PointCloud(vertices=mesh.vertices)
        else:
            return mesh

    vertices = np.asarray(mesh.vertices)
    if len(vertices) == 0:
        return mesh

    filter_config = config.get("filtering", {})
    enable_filter = filter_config.get("enable", True)
    if not enable_filter:
        return mesh

    print(f"   Filtering noise (initial: {len(vertices)} vertices)...")

    # Method 1: Statistical outlier removal
    # Remove points where average distance to k neighbors is > threshold
    k_neighbors = filter_config.get("k_neighbors", 20)
    std_ratio = filter_config.get("std_ratio", 2.0)

    try:
        from scipy.spatial import cKDTree
        tree = cKDTree(vertices)
        distances, _ = tree.query(vertices, k=k_neighbors + 1)  # +1 because point queries itself
        mean_distances = np.mean(distances[:, 1:], axis=1)  # Exclude self-distance
        mean_global = np.mean(mean_distances)
        std_global = np.std(mean_distances)
        threshold = mean_global + std_ratio * std_global
        mask = mean_distances < threshold
        vertices_filtered = vertices[mask]
        print(f"   After outlier removal: {len(vertices_filtered)} vertices")
    except ImportError:
        print("   [WARN] scipy not available, skipping outlier removal")
        vertices_filtered = vertices

    # Method 2: Keep only the largest dense cluster (the face)
    keep_largest_cluster = filter_config.get("keep_largest_cluster", True)
    if keep_largest_cluster and len(vertices_filtered) > 100:
        try:
            from sklearn.cluster import DBSCAN
            # Use adaptive eps based on point density
            # Estimate average nearest neighbor distance
            tree2 = cKDTree(vertices_filtered)
            nn_distances, _ = tree2.query(vertices_filtered, k=2)
            avg_nn_dist = np.mean(nn_distances[:, 1])  # Exclude self
            eps = avg_nn_dist * 3.0  # 3x average NN distance

            clustering = DBSCAN(eps=eps, min_samples=10).fit(vertices_filtered)
            labels = clustering.labels_

            # Find largest cluster (excluding noise label -1)
            unique, counts = np.unique(labels[labels >= 0], return_counts=True)
            if len(unique) > 0:
                largest_cluster = unique[np.argmax(counts)]
                mask_cluster = labels == largest_cluster
                vertices_filtered = vertices_filtered[mask_cluster]
                print(f"   After cluster filtering: {len(vertices_filtered)} vertices (largest cluster)")
        except (ImportError, Exception) as e:
            print(f"   [WARN] Cluster filtering failed: {e}")

    # Center the mesh at origin
    if len(vertices_filtered) > 0:
        center = np.mean(vertices_filtered, axis=0)
        vertices_filtered = vertices_filtered - center
        print(f"   Centered mesh (offset: {center})")

    return trimesh.PointCloud(vertices=vertices_filtered)


def _repair_mesh(mesh) -> None:
    """Fix bad vertex indices, degenerate faces, and unreferenced vertices.
    Handles both Trimesh (with faces) and PointCloud (vertices only) objects.
    """
    nv = len(mesh.vertices)
    if nv == 0:
        return

    # PointCloud objects don't have faces or process() method
    is_pointcloud = isinstance(mesh, trimesh.PointCloud)
    
    if is_pointcloud:
        # Point clouds: no repair needed, just ensure valid vertices
        return

    # Trimesh objects: repair faces and process
    has_faces = (
        hasattr(mesh, "faces")
        and mesh.faces is not None
        and len(mesh.faces) > 0
    )

    if has_faces:
        faces = np.asarray(mesh.faces)
        if faces.size > 0:
            max_idx = int(faces.max())
            if max_idx >= nv:
                valid = np.all(faces < nv, axis=1)
                mesh.update_faces(valid)
                mesh.remove_unreferenced_vertices()
        mesh.remove_degenerate_faces()
        mesh.remove_unreferenced_vertices()

    # Only Trimesh has process() method
    if hasattr(mesh, "process"):
        mesh.process()


def process_file(
    filename: str,
    input_folder: str,
    output_folder: str,
    config: dict,
) -> bool:
    """Process one PLY file. Returns True on success, False on failure."""
    input_path = os.path.join(input_folder, filename)
    output_filename = filename.replace(".ply", ".obj")
    output_path = os.path.join(output_folder, output_filename)

    print(f"Processing: {filename}")

    try:
        scene = trimesh.load(input_path, force="scene")
    except Exception as e:
        print(f"[FAIL] Load failed: {e}")
        return False

    if len(scene.geometry) == 0:
        print("[FAIL] No geometry found in scene.")
        return False

    mesh = scene.geometry[list(scene.geometry.keys())[0]]
    print(f"   Vertices: {len(mesh.vertices)}")

    # Filter noise for point clouds (real-world scans)
    if isinstance(mesh, trimesh.PointCloud):
        mesh = _filter_noise(mesh, config)

    mesh.visual = trimesh.visual.ColorVisuals(mesh)
    _repair_mesh(mesh)

    try:
        mesh.export(output_path)
    except Exception as e:
        print(f"[FAIL] Export failed: {e}")
        return False

    print(f"[OK] Saved: {output_filename} ({len(mesh.vertices)} vertices)\n")
    return True


def main() -> None:
    print("Rhinovate Sanitizer (one-pass)\n")

    config = _load_config()
    folders = config.get("folders", {})
    input_folder = folders.get("incoming", "1_Incoming")
    output_folder = folders.get("processing", "2_Processing")

    root = os.environ.get("RHINOVATE_PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(root, input_folder)
    output_dir = os.path.join(root, output_folder)

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    plies = [f for f in os.listdir(input_dir) if f.lower().endswith(".ply")]
    if not plies:
        print(f"[WARN] No .ply files in '{input_folder}'. Add scans and re-run.")
        sys.exit(1)

    failed = []
    for f in plies:
        if not process_file(f, input_dir, output_dir, config):
            failed.append(f)

    if failed:
        print(f"[FAIL] Failed: {', '.join(failed)}")
        sys.exit(1)

    print("[OK] Sanitizer finished.")


if __name__ == "__main__":
    main()
