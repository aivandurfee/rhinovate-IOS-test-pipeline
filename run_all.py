import subprocess
import os
import sys

# --- CONFIGURATION ---
# Path to your Blender executable (Same one you used before)
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"

# The two worker scripts
SANITIZER_SCRIPT = "sanitize_trimesh.py"
BLENDER_SCRIPT = "pipeline_final_v2.py"
# ---------------------

def main():
    print("==========================================")
    print("🚀 STARTING RHINOVATE PIPELINE")
    print("==========================================\n")

    # STEP 1: Run the Sanitizer (Standard Python)
    print(f"--- [Step 1/2] Running Sanitizer ({SANITIZER_SCRIPT}) ---")
    try:
        # We use sys.executable to ensure we use the CURRENT python (your venv)
        subprocess.run([sys.executable, SANITIZER_SCRIPT], check=True)
    except subprocess.CalledProcessError:
        print("❌ CRITICAL: Sanitizer failed. Stopping pipeline.")
        return

    print("\n✅ Sanitization complete. Handing off to Blender engine...\n")

    # STEP 2: Run the Blender Engine (Blender Python)
    print(f"--- [Step 2/2] Running Morphing Engine ({BLENDER_SCRIPT}) ---")
    try:
        subprocess.run([BLENDER_PATH, "--background", "--python", BLENDER_SCRIPT], check=True)
    except subprocess.CalledProcessError:
        print("❌ CRITICAL: Blender Engine failed.")
        return

    print("\n==========================================")
    print("🎉 PIPELINE FINISHED SUCCESSFULLY")
    print("   Output saved to: 3_Outgoing/healed_result.glb")
    print("==========================================")

if __name__ == "__main__":
    main()