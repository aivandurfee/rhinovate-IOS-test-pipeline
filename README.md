# Rhinovate iOS Pipeline (Prototype)

This repository contains the automated data processing pipeline for Rhinovate. It ingests raw LiDAR scans from iOS devices, sanitizes corrupted geometry, and generates a "healed" 3D morph prediction using a headless Blender engine.

## 🚀 Architecture

The pipeline runs in two autonomous stages:

1.  **Ingest & Sanitize (`sanitize_trimesh.py`)**
    * **Input:** Raw `.ply` point cloud (iOS LiDAR export).
    * **Action:** Detects and repairs "Bad Vertex Index" errors; strips corrupted color headers.
    * **Output:** Cleaned, compliant `.obj` geometry.

2.  **Voxelization & Morphing (`pipeline_final_v2.py`)**
    * **Engine:** Blender 5.0 (Headless Mode).
    * **Action:** Converts the Point Cloud into a watertight mesh using Voxel Remeshing (Geometry Nodes), applies a procedural taper deformation, and exports to mobile-ready glTF.
    * **Output:** `.glb` 3D model.

## 🛠️ How to Run

1.  **Install Dependencies:**
    ```bash
    pip install trimesh
    ```
2.  **Configure Blender Path:**
    * Open `run_all.py` and update `BLENDER_PATH` to your local installation.
3.  **Run the Pipeline:**
    ```bash
    python run_all.py
    ```
    * Place raw scans in `1_Incoming/`.
    * Collect results from `3_Outgoing/`.

## 📂 File Structure

* `run_all.py` - Master script that orchestrates the Python and Blender workers.
* `sanitize_trimesh.py` - Python worker for file repair.
* `pipeline_final_v2.py` - Blender Python script for meshing and morphing.