import os
import sys
import time
import subprocess
import shutil

# Drive L: for Navidrome Music
MOUNT_POINT = "P:" 
POD_PATH = "/stash/" 


def load_env():
    """Load root .env file into os.environ."""
    env_file = os.path.abspath(os.path.join(os.getcwd(), "../../.env"))
    if os.path.exists(env_file):
        print(f"[Proxion] Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
                    if key == "MEDIA_MUSIC":
                        print(f"[Proxion] Detected MEDIA_MUSIC={value}")
    else:
        print("[Proxion] WARNING: Root .env file not found!")

def is_mounted(drive):
    return os.path.exists(drive)

def run_mount():
    """Start the FUSE mount on Drive P:"""
    if is_mounted(MOUNT_POINT):
        print(f"[Proxion] {MOUNT_POINT} is already mounted. Skipping.")
        return None
        
    print(f"[Proxion] Mounting Drive {MOUNT_POINT} ...")
    fuse_script = os.path.abspath(os.path.join(os.getcwd(), "../../proxion-fuse/mount.py"))
    # Use the discovered STASH_ROOT or fall back to the config within mount.py
    cmd = ["python", fuse_script, MOUNT_POINT]
    return subprocess.Popen(cmd, env=os.environ.copy())

def start_docker():
    """Start Navidrome."""
    print("[Proxion] Starting Navidrome...")
    
    yml_file = os.path.join(os.getcwd(), "docker-compose.yml")
    tmp_yml = os.path.join(os.getcwd(), "docker-compose.tmp.yml")
    
    with open(yml_file, 'r') as f:
        content = f.read()
    
    # Simple interpolation
    content = content.replace("${MEDIA_MUSIC}", os.environ.get("MEDIA_MUSIC", ""))
    content = content.replace("${STASH_ROOT}", os.environ.get("STASH_ROOT", ""))
    
    with open(tmp_yml, 'w') as f:
        f.write(content)
        
    subprocess.run(["docker-compose", "-f", tmp_yml, "up", "-d"], check=True, env=os.environ.copy())

def stop_docker():
    print("[Proxion] Stopping Navidrome...")
    tmp_yml = os.path.join(os.getcwd(), "docker-compose.tmp.yml")
    if os.path.exists(tmp_yml):
        subprocess.run(["docker-compose", "-f", tmp_yml, "down"], check=False, env=os.environ.copy())
        os.remove(tmp_yml)
    else:
        subprocess.run(["docker-compose", "down"], check=False, env=os.environ.copy())

def main():
    load_env()
    mount_process = None
    
    try:
        mount_process = run_mount()
        # Wait for mount to stabilize
        time.sleep(3)
        
        if mount_process and mount_process.poll() is not None:
            print("Error: FUSE Mount failed to start.")
            sys.exit(1)
            
        start_docker()
        
        print("\n[Proxion] Navidrome is RUNNING at http://localhost:4533")
        print(f"Proxion Music: {MOUNT_POINT} (Pod) -> /music (Docker)")
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
