
import requests
import json
import os

AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def main():
    print("--- Patching Calibre Provider ---")
    
    # 1. Get Provider
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/providers/proxy/", headers=HEADERS, params={"search": "Calibre"})
    results = resp.json().get("results", [])
    if not results:
        print("❌ Calibre Provider not found!")
        return
    
    provider = results[0]
    pk = provider['pk']
    print(f"✅ Found Provider: {provider['name']} (pk={pk})")
    print(f"   Current External Host: {provider['external_host']}")
    
    # 2. Update to Regex to allow localhost AND 127.0.0.1
    # Authentik matching via regex if it starts logic
    new_host = "http://(localhost|127\\.0\\.0\\.1):8083"
    
    data = {
        "external_host": new_host
    }
    
    resp = requests.patch(f"{AUTHENTIK_URL}/api/v3/providers/proxy/{pk}/", headers=HEADERS, json=data)
    
    if resp.status_code < 400:
        print(f"✅ FIXED: Updated external_host to {new_host}")
    else:
        print(f"❌ Failed to update provider: {resp.text}")

if __name__ == "__main__":
    main()
