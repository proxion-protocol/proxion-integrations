import os
import sys
import bcrypt
import yaml # We'll need PyYAML or just use string replacement if not available
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ed25519

# Paths
INTEGRATION_DIR = os.path.dirname(os.path.abspath(__file__))
CONF_DIR = os.path.abspath(os.path.join(INTEGRATION_DIR, "../../proxion-core/storage/network/adguard/conf"))
YAML_PATH = os.path.join(CONF_DIR, "AdGuardHome.yaml")
KEY_PATH = os.path.abspath(os.path.join(INTEGRATION_DIR, "../../proxion-keyring/identity_private.pem"))

def derive_app_password(key_path, app_name):
    with open(key_path, "rb") as f:
        master_key = serialization.load_pem_private_key(f.read(), password=None)
    
    raw_bytes = master_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=16,
        salt=None,
        info=f"app:password:{app_name}".encode(),
    )
    derived = hkdf.derive(raw_bytes)
    return derived.hex()[:16]

def main():
    if not os.path.exists(KEY_PATH):
        print(f"Error: Identity key not found at {KEY_PATH}")
        sys.exit(1)
    
    password = derive_app_password(KEY_PATH, "adguard")
    print(f"Derived Password for AdGuard: {password}")
    
    # Hash password with Bcrypt (AdGuard format)
    # AdGuard expects $2a$ or $2b$
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()
    
    if not os.path.exists(YAML_PATH):
        print(f"Error: AdGuardHome.yaml not found at {YAML_PATH}")
        sys.exit(1)
        
    print(f"Provisioning user 'proxion' in {YAML_PATH}...")
    
    with open(YAML_PATH, "r") as f:
        content = f.read()
    
    # Simple YAML update logic without needing PyYAML (to be safe about dependencies)
    # We want to replace 'users: []' or add to it.
    user_entry = f"""users:
  - name: proxion
    password: {hashed}
"""
    
    if "users: []" in content:
        new_content = content.replace("users: []", user_entry)
    elif "users:" in content:
        # Check if already exists
        if "name: proxion" in content:
            print("User 'proxion' already exists. Updating password.")
            # This is harder to do with regex, but let's try a simple approach
            import re
            new_content = re.sub(r"name: proxion\n    password: .*", f"name: proxion\n    password: {hashed}", content)
        else:
            new_content = content.replace("users:", user_entry)
    else:
        new_content = content + "\n" + user_entry
        
    with open(YAML_PATH, "w") as f:
        f.write(new_content)
        
    print("Successfully provisioned User: proxion")
    print("Please restart AdGuard to apply changes: docker-compose restart adguardhome")

if __name__ == "__main__":
    main()
