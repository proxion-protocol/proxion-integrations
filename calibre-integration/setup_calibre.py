import os
import sys
import time
import subprocess

# Add keyring paths for identity
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../proxion-keyring")))
try:
    from proxion_keyring.identity import load_or_create_identity_key, derive_app_password
except ImportError:
    print("[Calibre] Warning: Could not import proxion_keyring.identity.")
    print("[Calibre] Falling back to default password.")
    
def get_deterministic_password():
    try:
        # Path to identity_private.pem matches provision_adguard.py logic
        key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../proxion-keyring/proxion_keyring/identity_private.pem"))
        if not os.path.exists(key_path):
             print(f"[Calibre] Identity key not found at {key_path}")
             return "Proxion123!" # Fallback
        
        master_key = load_or_create_identity_key(key_path)
        return derive_app_password(master_key, "calibre")
    except Exception as e:
        print(f"[Calibre] Derivation failed: {e}")
        return "Proxion123!"

def main():
    print("[Calibre] Starting container for configuration...")
    
    # 1. Smart Start
    try:
        cmd = ["docker-compose", "-f", "docker-compose.yml"]
        if os.path.exists("docker-compose.proxion-local.yml"):
             cmd += ["-f", "docker-compose.proxion-local.yml"]
        elif os.path.exists("docker-compose.override.yml"):
             cmd += ["-f", "docker-compose.override.yml"]
        cmd += ["up", "-d"]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"[Calibre] Failed to start container: {e}")
        return

    # 2. Get Password
    admin_password = get_deterministic_password()
    print(f"[Calibre] Using deterministic password: {admin_password}")

    # 3. Setup Script
    setup_code = """
import sqlite3
import sys
try:
    from werkzeug.security import generate_password_hash
except ImportError:
    print("Werkzeug fail")
    sys.exit(1)

con = sqlite3.connect('/config/app.db')
cur = con.cursor()

try:
    # 1. Anon Browsing
    try:
        cur.execute("UPDATE settings SET config_anon_browsing = 1")
        print("Anon Browsing: OK")
    except Exception:
        pass # Ignore missing column
    
    # 2. Path (Crucial)
    try:
        cur.execute("UPDATE settings SET config_calibre_dir = '/books'")
        print("Path: OK")
    except Exception as e:
        print(f"Path: FAIL ({e})")
    
    
    # 3. Password
    try:
        pw = generate_password_hash('__PASSWORD__')
        # Corrected: column is 'name' not 'nickname'
        cur.execute("UPDATE user SET password = ? WHERE name = 'admin'", (pw,))
        if cur.rowcount > 0:
            print("Password: OK")
        else:
            print("Password: FAIL (User not updated)")
    except Exception as e:
        print(f"Password: FAIL ({e})")

    # 4. Reverse Proxy SSO (Auto-Enable)
    try:
        cur.execute("UPDATE settings SET config_allow_reverse_proxy_header_login = 1")
        cur.execute("UPDATE settings SET config_reverse_proxy_login_header_name = 'X-authentik-username'")
        print("SSO: OK")
    except Exception as e:
        print(f"SSO: FAIL ({e})")
    
    con.commit()
    con.close()
    print("SUCCESS_DONE")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
"""
    setup_code = setup_code.replace("__PASSWORD__", admin_password)

    print("[Calibre] Configuring User and Library...")
    # Pipe to Docker
    cmd = ["docker", "exec", "-i", "calibre-web", "python3", "-"]
    for attempt in range(5):
        try:
            res = subprocess.run(cmd, input=setup_code, capture_output=True, text=True)
            if res.returncode == 0 and "SUCCESS_DONE" in res.stdout:
                print("[Calibre] Configuration Applied!")
                print(f"[Calibre] \u2705 Admin Password set to: {admin_password}")
                if "Path: OK" in res.stdout:
                    print("[Calibre] \u2705 Library Path set to /books")
                return
            else:
                if attempt == 4:
                    print(f"[Calibre] Configuration Failed: {res.stdout} {res.stderr}")
        except Exception as e:
            print(f"[Calibre] Exec Error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
