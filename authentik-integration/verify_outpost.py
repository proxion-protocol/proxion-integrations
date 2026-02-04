
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
    print("--- Verifying Authentik Config ---")
    
    # 1. Get Outpost
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/outposts/instances/", headers=HEADERS)
    outposts = resp.json().get("results", [])
    print(f"DEBUG: Found {len(outposts)} outposts")
    for o in outposts:
        print(f" - {o['name']} (type={o['type']}, pk={o['pk']})")
        
    embedded = next((o for o in outposts if o['type'] == 'proxy' or 'embedded' in o['name'].lower()), None)
    
    if not embedded:
        print("❌ Certified Panic: Embedded Outpost not found!")
        return

    print(f"✅ Found Outpost: {embedded['name']} (pk={embedded['pk']})")
    print(f"   Attached Providers: {embedded['providers']}")
    
    # 2. Get Calibre Provider
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/providers/proxy/", headers=HEADERS, params={"search": "Calibre"})
    results = resp.json().get("results", [])
    if not results:
        print("❌ Calibre Provider not found!")
        return
        
    provider = results[0]
    print(f"✅ Found Provider: {provider['name']} (pk={provider['pk']})")
    print(f"   External Host: {provider['external_host']}")
    print(f"   Internal Host: {provider['internal_host']}")
    
    # 3. Fix Attachment
    if provider['pk'] not in embedded['providers']:
        print("⚠️ Provider NOT in Outpost! Fixing...")
        current_providers = embedded['providers']
        current_providers.append(provider['pk'])
        resp = requests.patch(f"{AUTHENTIK_URL}/api/v3/outposts/instances/{embedded['pk']}/", headers=HEADERS, json={"providers": current_providers})
        if resp.status_code < 400:
            print("✅ FIXED: Provider added to outpost.")
        else:
            print(f"❌ Failed to update outpost: {resp.text}")
    else:
        print("✅ Provider is correctly attached to outpost.")

    # 4. Fix Host mismatch if any
    # Nginx sends Host: localhost (or localhost:8083). Provider expects http://localhost:8083
    # Note: Authentik removes scheme for matching usually.
    pass

if __name__ == "__main__":
    main()
