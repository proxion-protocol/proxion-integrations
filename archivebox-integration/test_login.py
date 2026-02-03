
import requests
import re
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path to import proxion_keyring modules if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../proxion-keyring')))
from proxion_keyring.identity import load_or_create_identity_key, derive_app_password

def test_login():
    base_url = "http://127.0.0.1:8090"
    login_url = f"{base_url}/admin/login/"
    admin_url = f"{base_url}/admin/"
    
    # 1. Derive password
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../proxion-keyring/proxion_keyring/identity_private.pem'))
    master_key = load_or_create_identity_key(key_path)
    password = derive_app_password(master_key, "archivebox")
    username = "admin"
    
    print(f"Testing login with {username} / {password}...")
    
    session = requests.Session()
    
    # 2. Get Login Page for CSRF
    resp = session.get(login_url)
    print(f"GET {login_url} -> {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if not csrf_input:
        print("Error: No CSRF token found in form")
        return
        
    # Inspect Form
    print("Form inputs found:")
    for inp in soup.find_all('input'):
        print(f" - {inp.get('name')} (type={inp.get('type')})")
        
    csrf_token = csrf_input['value']
    print(f"CSRF Token: {csrf_token[:10]}...")
    
    # 3. POST Login
    payload = {
        'username': username,
        'password': password,
        'csrfmiddlewaretoken': csrf_token,
        'next': '/admin/'
    }
    
    headers = {
        'Referer': login_url,
        'Origin': base_url
    }
    
    resp = session.post(login_url, data=payload, headers=headers)
    print(f"POST {login_url} -> {resp.status_code}")
    
    with open("login_response.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved response to login_response.html")
    
    if session.cookies.get('sessionid'):
        print("SUCCESS: Got sessionid cookie!")
        print(f"sessionid: {session.cookies.get('sessionid')}")
        print(f"csrftoken: {session.cookies.get('csrftoken')}")
    else:
        print("FAILURE: No sessionid cookie received.")
        if "Please enter a correct username and password" in resp.text:
            print("ERROR: Invalid credentials")
        else:
            print("Response text snippet:")
            print(resp.text[:500])

if __name__ == "__main__":
    try:
        test_login()
    except Exception as e:
        print(f"Exception: {e}")
