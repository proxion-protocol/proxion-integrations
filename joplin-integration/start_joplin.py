import os
import sys
import time
import subprocess
import threading
import requests

# Drive Y: for Joplin Notes
MOUNT_POINT = "P:" 
POD_PATH = "/stash/" # Target directory in the Solid Pod


def is_mounted(drive):
    return os.path.exists(drive)

def run_mount():
    """Start the FUSE mount on Drive P:"""
    if is_mounted(MOUNT_POINT):
        print(f"[Proxion] {MOUNT_POINT} is already mounted. Skipping.")
        return None
        
    print(f"[Proxion] Mounting Pod {POD_PATH} to {MOUNT_POINT} ...")
    fuse_script = os.path.abspath(os.path.join(os.getcwd(), "../../proxion-fuse/mount.py"))
    cmd = ["python", fuse_script, MOUNT_POINT, POD_PATH]
    return subprocess.Popen(cmd)

def start_docker():
    """Start Joplin containers."""
    print("[Proxion] Starting Joplin Server...")
    # Ensure the local 'storage' directory is mapped to the FUSE mount
    # On Windows, we can use a junction or just rely on the docker-compose mapping
    # However, Docker Desktop can be picky about mounting Drive letters.
    # A safer way is to mount FUSE to a folder inside joplin-integration/storage
    subprocess.run(["docker-compose", "up", "-d"], check=True)

def stop_docker():
    print("[Proxion] Stopping Joplin...")
    subprocess.run(["docker-compose", "down"], check=True)

def main():
    mount_process = None
    # Ensure storage dir exists
    if not os.path.exists("storage"):
        os.makedirs("storage")
        
    try:
        # 1. Mount FUSE
        # Note: In a real scenario, we might want to mount directly to the 'storage' folder
        # but for consistency with Immich, we'll use a drive letter first.
        mount_process = run_mount()
        time.sleep(2) # Give it a moment to mount
        
        if mount_process and mount_process.poll() is not None:
            print("Error: FUSE Mount failed to start.")
            # Fallback or exit
            sys.exit(1)
            
        # 2. Start Joplin
        start_docker()
        
        print("\n[Proxion] Joplin Server is RUNNING at http://localhost:22300")
        print(f"Storage Logic: Joplin (Docker) -> ./storage -> {MOUNT_POINT} (FUSE) -> Pod")
        print("Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            if mount_process and mount_process.poll() is not None:
                print("Error: FUSE Mount crashed!")
                break
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stop_docker()
        if mount_process:
            mount_process.terminate()

if __name__ == "__main__":
    main()
