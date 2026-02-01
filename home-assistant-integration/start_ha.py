import os
import sys
import time
import subprocess
import threading

# Drive W: for Home Assistant Config
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
    """Start Home Assistant container."""
    print("[Proxion] Starting Home Assistant...")
    # HA in host mode on Windows might have limitations, but we follow the Spec/Vision.
    subprocess.run(["docker-compose", "up", "-d"], check=True)

def stop_docker():
    print("[Proxion] Stopping Home Assistant...")
    subprocess.run(["docker-compose", "down"], check=True)

def main():
    mount_process = None
    # Ensure local config dir exists (as a mount point/fallback)
    if not os.path.exists("config"):
        os.makedirs("config")
        
    try:
        # 1. Mount FUSE
        mount_process = run_mount()
        time.sleep(2) # Give it a moment to mount
        
        if mount_process and mount_process.poll() is not None:
            print("Error: FUSE Mount failed to start.")
            sys.exit(1)
            
        # 2. Start Home Assistant
        start_docker()
        
        print("\n[Proxion] Home Assistant is RUNNING at http://localhost:8123")
        print(f"Config Logic: HA (Docker) -> /config -> {MOUNT_POINT} (FUSE) -> Pod")
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
