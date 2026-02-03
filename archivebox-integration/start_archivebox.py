#!/usr/bin/env python3
"""
ArchiveBox Auto-Configuration Script
Automatically creates admin user on first install (non-interactive)
Uses deterministic password derived from master identity key (same as AdGuard)
"""
import subprocess
import time
import sys
import os
import tempfile

# Add parent directory to path to import proxion_keyring modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../proxion-keyring')))

from proxion_keyring.identity import load_or_create_identity_key, derive_app_password

CONTAINER_NAME = "archivebox-integration-archivebox-1"
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@localhost"

# Derive deterministic password from master identity key
def get_admin_password():
    """Derive deterministic password for ArchiveBox using master identity key"""
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                             '../../proxion-keyring/proxion_keyring/identity_private.pem'))
    master_key = load_or_create_identity_key(key_path)
    return derive_app_password(master_key, "archivebox")

ADMIN_PASSWORD = get_admin_password()

def wait_for_container(max_wait=60):
    """Wait for container to be fully ready"""
    print("[ArchiveBox] Waiting for container to be ready...")
    for i in range(max_wait):
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )
            if "Up" in result.stdout:
                print(f"[ArchiveBox] Container is running, waiting for Django...")
                time.sleep(5)
                return True
        except subprocess.CalledProcessError:
            pass
        time.sleep(1)
    return False

def create_superuser_automated():
    """Create superuser using a temporary Python script"""
    print(f"[ArchiveBox] Creating admin user '{ADMIN_USERNAME}'...")
    
    # Create a Python script to run inside the container
    python_script = f"""from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.filter(username='{ADMIN_USERNAME}').exists():
    u = User.objects.get(username='{ADMIN_USERNAME}')
    u.set_password('{ADMIN_PASSWORD}')
    u.email = '{ADMIN_EMAIL}'
    u.save()
    print('UPDATED')
else:
    User.objects.create_superuser('{ADMIN_USERNAME}', '{ADMIN_EMAIL}', '{ADMIN_PASSWORD}')
    print('CREATED')
"""
    
    # Write script to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_script)
        temp_script = f.name
    
    try:
        # Copy script into container
        subprocess.run(
            ["docker", "cp", temp_script, f"{CONTAINER_NAME}:/tmp/create_user.py"],
            check=True,
            capture_output=True
        )
        
        # Run script inside container using stdin
        result = subprocess.run(
            ["docker", "exec", "-i", "--user=archivebox", CONTAINER_NAME, 
             "archivebox", "manage", "shell"],
            input=python_script,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Clean up
        subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "rm", "-f", "/tmp/create_user.py"],
            capture_output=True
        )
        
        if "CREATED" in output:
            print(f"[ArchiveBox] SUCCESS: Admin user created!")
            print_credentials()
            return True
        elif "UPDATED" in output:
            print(f"[ArchiveBox] SUCCESS: Admin user password updated!")
            print_credentials()
            return True
        else:
            print(f"[ArchiveBox] WARNING: Unexpected output")
            print(f"Output: {output[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[ArchiveBox] WARNING: Timeout while creating superuser")
        return False
    except Exception as e:
        print(f"[ArchiveBox] WARNING: Error: {e}")
        return False
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_script)
        except:
            pass

def print_credentials():
    """Print login credentials"""
    print(f"[ArchiveBox]")
    print(f"[ArchiveBox] Login Credentials:")
    print(f"[ArchiveBox]    URL: http://127.0.0.1:8090")
    print(f"[ArchiveBox]    Username: {ADMIN_USERNAME}")
    print(f"[ArchiveBox]    Password: {ADMIN_PASSWORD}")
    print(f"[ArchiveBox]")

def main():
    print("=" * 70)
    print("[ArchiveBox] Auto-Configuration Starting...")
    print("=" * 70)
    
    if not wait_for_container():
        print("[ArchiveBox] ERROR: Container failed to start within timeout")
        sys.exit(1)
    
    if create_superuser_automated():
        print("[ArchiveBox] SUCCESS: Auto-configuration complete!")
        print("[ArchiveBox]")
        print("[ArchiveBox] Next Steps:")
        print("[ArchiveBox]    1. Install Firefox extension:")
        print("[ArchiveBox]       https://addons.mozilla.org/firefox/addon/archivebox-exporter/")
        print("[ArchiveBox]    2. Configure extension URL: http://127.0.0.1:8090")
        print("[ArchiveBox]    3. Start archiving!")
    else:
        print("[ArchiveBox] WARNING: Auto-configuration had issues")
        print("[ArchiveBox]    Manual setup:")
        print(f"[ArchiveBox]    docker exec -it --user=archivebox {CONTAINER_NAME} archivebox manage createsuperuser")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
