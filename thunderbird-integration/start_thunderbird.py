import os
import sys
import time
import subprocess

# Drive O: for Thunderbird Attachments (FileLink)
MOUNT_POINT = "P:" 
POD_PATH = "/stash/" 


def is_mounted(drive):
    return os.path.exists(drive)

def run_mount():
    if is_mounted(MOUNT_POINT):
        print(f"[Proxion] {MOUNT_POINT} is already mounted. Skipping.")
        return None
    fuse_script = os.path.abspath(os.path.join(os.getcwd(), "../../proxion-fuse/mount.py"))
    cmd = ["python", fuse_script, MOUNT_POINT, POD_PATH]
    return subprocess.Popen(cmd)

def main():
    mount_process = None
    try:
        mount_process = run_mount()
        time.sleep(2)
        
        if mount_process and mount_process.poll() is not None:
            print("Error: FUSE Mount failed to start.")
            sys.exit(1)
            
        print("\n[Proxion] Proxion Mail Storage is READY.")
        print(f"Mount Point: {MOUNT_POINT} (Pod)")
        print("\nINSTRUCTIONS for Thunderbird:")
        print("1. Open Thunderbird -> Settings -> Composition -> General.")
        print("2. Under 'Attachments', click 'Add [Cloud Provider]'.")
        print("3. Use the 'Local Folder' provider (if installed) or point a custom extension to:")
        print(f"   {MOUNT_POINT}\\")
        print("\nLarge attachments will now be stored in your Solid Pod instead of your e-mail provider.")
        print("Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            if mount_process and mount_process.poll() is not None:
                print("Error: FUSE Mount crashed!")
                break
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if mount_process:
            mount_process.terminate()

if __name__ == "__main__":
    main()
