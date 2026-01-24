"""
Rhinovate pipeline orchestrator.
Runs sanitizer then Blender morph engine. Uses config.json for paths and params.
"""
import json
import os
import subprocess
import sys

CONFIG_PATH = "config.json"
SANITIZER_SCRIPT = "sanitize_trimesh.py"
BLENDER_SCRIPT = "pipeline_hd.py"


def load_config(project_root: str) -> dict:
    path = os.path.join(project_root, CONFIG_PATH)
    if not os.path.isfile(path):
        print(f"[FAIL] Config not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    config = load_config(project_root)
    folders = config.get("folders", {})
    inc = folders.get("incoming", "1_Incoming")
    proc = folders.get("processing", "2_Processing")
    out = folders.get("outgoing", "3_Outgoing")

    for rel_path in (inc, proc, out):
        os.makedirs(os.path.join(project_root, rel_path), exist_ok=True)

    env = os.environ.copy()
    env["RHINOVATE_PROJECT_ROOT"] = project_root

    print("==========================================")
    print("RHINOVATE PIPELINE")
    print("==========================================\n")

    print(f"--- [Step 1/2] Sanitizer ({SANITIZER_SCRIPT}) ---")
    try:
        subprocess.run(
            [sys.executable, SANITIZER_SCRIPT],
            check=True,
            cwd=project_root,
            env=env,
        )
    except subprocess.CalledProcessError:
        print("[FAIL] Sanitizer failed. Stopping pipeline.")
        sys.exit(1)

    print("\n[OK] Sanitization complete. Handing off to Blender...\n")

    blender_path = config.get("blender_path")
    if not blender_path or not os.path.isfile(blender_path):
        print(f"[FAIL] Blender not found: {blender_path}")
        print("   Update blender_path in config.json.")
        sys.exit(1)

    print(f"--- [Step 2/2] Morph engine ({BLENDER_SCRIPT}) ---")
    try:
        subprocess.run(
            [blender_path, "--background", "--python", BLENDER_SCRIPT],
            check=True,
            cwd=project_root,
            env=env,
        )
    except subprocess.CalledProcessError:
        print("[FAIL] Blender engine failed.")
        sys.exit(1)

    print("\n==========================================")
    print("PIPELINE FINISHED")
    print(f"   Output: {out}/ (*_healed.glb)")
    print("==========================================")


if __name__ == "__main__":
    main()
