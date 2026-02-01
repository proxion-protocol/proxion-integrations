import os
import sys
import time
import subprocess
import threading
import signal
import requests
import json

IMMICH_URL = "http://localhost:2283"
ADMIN_EMAIL = "admin@proxion.local"
ADMIN_PASS = "ProxionProxion123!"


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
    """Start Immich containers."""
    print("[Proxion] Starting Immich Containers...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)

def stop_docker():
    print("[Proxion] Stopping Immich...")
    subprocess.run(["docker-compose", "down"], check=True)

def bootstrap_immich():
    """
    Zero-Config:
    1. Wait for API
    2. Register Default Admin
    3. Login
    4. Create External Library pointing to FUSE mount
    """
    print("[Proxion] Waiting for Immich API...")
    for _ in range(30): # Wait up to 60s
        try:
            requests.get(f"{IMMICH_URL}/api/server-info/ping", timeout=2)
            break
        except:
            time.sleep(2)
    else:
        print("[Proxion] Warning: Immich did not respond in time.")
        return

    print("[Proxion] Bootstrapping configuration...")
    
    # 1. Register (Ignore if exists)
    try:
        requests.post(f"{IMMICH_URL}/api/auth/admin-register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASS,
            "name": "Proxion User"
        })
    except:
        pass # Already exists
        
    # 2. Login
    token = None
    try:
        res = requests.post(f"{IMMICH_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASS
        })
        if res.status_code == 201:
            token = res.json().get("accessToken")
    except Exception as e:
        print(f"[Proxion] Login failed: {e}")
        return

    if not token:
        print("[Proxion] Could not log in. Skipping library setup.")
        return

    # 3. Create External Library
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check if exists
    libs = requests.get(f"{IMMICH_URL}/api/library", headers=headers).json()
    has_fuse = any(l.get("name") == "Proxion Pod" for l in libs)
    
    if not has_fuse:
        print("[Proxion] Creating External Library 'Proxion Pod'...")
        # Note: endpoint payload structure varies by version, assuming v1.90+ standard
        requests.post(f"{IMMICH_URL}/api/library", headers=headers, json={
            "name": "Proxion Pod",
            "type": "EXTERNAL",
            "importPaths": ["/usr/src/app/upload"]
        })
        print("[Proxion] Library Configured!")
    else:
        print("[Proxion] Library 'Proxion Pod' already exists.")

def main():
    mount_process = None
    try:
        # 1. Mount FUSE
        mount_process = run_mount()
        time.sleep(2) # Give it a moment to mount
        
        if mount_process and mount_process.poll() is not None:
            print("Error: FUSE Mount failed to start.")
            sys.exit(1)
            
        # 2. Start Immich
        start_docker()
        
        # 3. Bootstrap
        threading.Thread(target=bootstrap_immich, daemon=True).start()
        
        print("\n[Proxion] Immich is RUNNING.")
        print("Photos Logic: Immich (Docker) -> Z:/ (FUSE) -> Proxion Proxy -> Pod")
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
