import os
import sys
import time
import subprocess

# Drive N: for Paperless-ngx Documents
MOUNT_POINT = "P:" 
POD_PATH = "/stash/" 


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
    """Start Paperless-ngx."""
    print("[Proxion] Starting Paperless-ngx Stack...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)

def stop_docker():
    print("[Proxion] Stopping Paperless-ngx Stack...")
    subprocess.run(["docker-compose", "down"], check=True)

def main():
    mount_process = None
    
    try:
        mount_process = run_mount()
        time.sleep(2)
        
        if mount_process and mount_process.poll() is not None:
            print("Error: FUSE Mount failed to start.")
            sys.exit(1)
            
        start_docker()
        
        print("\n[Proxion] Paperless-ngx is RUNNING at http://localhost:8000")
        print(f"Proxion Documents: {MOUNT_POINT} (Pod) -> /media, /data, /consume (Docker)")
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
