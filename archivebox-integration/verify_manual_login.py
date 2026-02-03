#!/usr/bin/env python3
"""
Quick verification that the auto-generated password works for manual browser login.
This just prints the credentials that should work.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../proxion-keyring')))
from proxion_keyring.identity import load_or_create_identity_key, derive_app_password

def main():
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                             '../../proxion-keyring/proxion_keyring/identity_private.pem'))
    master_key = load_or_create_identity_key(key_path)
    password = derive_app_password(master_key, "archivebox")
    
    print("=" * 60)
    print("ArchiveBox Login Credentials")
    print("=" * 60)
    print(f"URL:      http://127.0.0.1:8090")
    print(f"Username: admin")
    print(f"Password: {password}")
    print("=" * 60)
    print("\nThese credentials were set by start_archivebox.py")
    print("Try logging in manually with these in your browser.")

if __name__ == "__main__":
    main()
