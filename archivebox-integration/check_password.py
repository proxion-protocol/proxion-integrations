#!/usr/bin/env python3
"""
Check the actual password hash in the ArchiveBox database
"""
import subprocess
import sys

# Script to run inside the container
check_script = """
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    u = User.objects.get(username='admin')
    print(f'User: {u.username}')
    print(f'Email: {u.email}')
    print(f'Is staff: {u.is_staff}')
    print(f'Is superuser: {u.is_superuser}')
    print(f'Password hash (first 50 chars): {u.password[:50]}...')
    
    # Test if password matches
    from django.contrib.auth.hashers import check_password
    test_pw = '941b003ce5309c43'
    matches = u.check_password(test_pw)
    print(f'Password matches {test_pw}: {matches}')
except User.DoesNotExist:
    print('User does not exist!')
"""

# Run it
cmd = [
    "docker", "exec", "--user=archivebox", 
    "archivebox-integration-archivebox-1",
    "bash", "-c",
    f'echo "{check_script}" | archivebox shell'
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Exit code:", result.returncode)
