# Rhinovate iOS Pipeline

Automated data processing pipeline for **Rhinovate**: ingests raw LiDAR scans from iOS, sanitizes geometry, and produces a morphed 3D prediction (GLB) via a headless Blender engine.

## Architecture

The pipeline runs in two stages, orchestrated by `run_all.py`:

1. **Ingest & Sanitize** (`sanitize_trimesh.py`)
   - **Input:** Raw `.ply` point clouds (iOS LiDAR export).
   - **Actions:** Load as scene; strip broken color data; repair bad vertex indices, degenerate faces, and unreferenced vertices; export clean geometry.
   - **Output:** `.obj` files in `2_Processing/`.

2. **Morph Engine** (`pipeline_hd.py`, Blender headless)
   - **Input:** Sanitized `.obj` from `2_Processing/`.
   - **Actions:** Import OBJ; optionally voxelize (Mesh→Points→Volume→Mesh) for watertight meshes; apply lattice-based nose morph; export with modifiers applied.
   - **Output:** `*_healed.glb` in `3_Outgoing/`.

## Configuration

Paths and morph parameters are read from **`config.json`** in the project root. `run_all.py` sets `RHINOVATE_PROJECT_ROOT` and uses `config.json` for:

- **`blender_path`** — Path to Blender executable (e.g. Blender 5.0).
- **`folders`** — `incoming`, `processing`, `outgoing` (defaults: `1_Incoming`, `2_Processing`, `3_Outgoing`).
- **`pipeline`** — `use_voxelization`, `voxel_radius`, `voxel_amount`, `volume_threshold`, `volume_adaptivity`, `lattice_points`, `lattice_padding`, `lattice_resize_x`, `lattice_brush_factor`.

Update `blender_path` and any morph defaults as needed for your environment.

## How to Run

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   (Requires `numpy` and `trimesh`.)

2. **Configure**
   - Edit `config.json`: set `blender_path` to your Blender install.
   - Place raw `.ply` scans in `1_Incoming/` (or your configured `incoming` folder).

3. **Run the pipeline**
   ```bash
   python run_all.py
   ```
   - Sanitizer runs first; on failure, the pipeline stops.
   - Blender morph engine runs next; output is written to `3_Outgoing/` (or your configured `outgoing` folder).

4. **Output**
   - Collect `*_healed.glb` from `3_Outgoing/` for use on iOS.

## File Structure

- `run_all.py` — Orchestrator: loads config, creates folders, runs sanitizer then Blender, fail-fast on errors.
- `sanitize_trimesh.py` — Python worker: PLY → cleaned OBJ.
- `pipeline_hd.py` — Blender Python script: OBJ → morphed GLB (lattice; optional voxelization).
- `config.json` — Paths and pipeline parameters.

## Notes

- The pipeline uses **explicit project root** (`RHINOVATE_PROJECT_ROOT` / `config.json`). Blender is invoked with `cwd` set to the project root so paths resolve correctly.
- Sanitizer and Blender script **exit with non-zero** on fatal errors; `run_all` stops immediately.
- **Voxelization** is off by default (`use_voxelization: false`). Enable it in `config.json` for watertight meshes from sparse point clouds (e.g. iPhone LiDAR).
