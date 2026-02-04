
"""
Configure Authentik for Calibre-Web SSO using direct API calls.
"""

import requests
import json
import sys

# Configuration
AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"
FLOW_PK = "cda727f9-4385-4550-b649-75608bb0278f"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_provider_pk():
    """Get existing or create new Proxy Provider."""
    # Check if exists
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/providers/proxy/", headers=HEADERS, params={"search": "Calibre Provider"})
    resp.raise_for_status()
    results = resp.json().get("results", [])
    
    if results:
        print(f"Provider already exists: {results[0]['pk']}")
        return results[0]['pk']
    
    # Create
    data = {
        "name": "Calibre Provider",
        "authorization_flow": FLOW_PK,
        "external_host": "http://localhost:8083",
        "internal_host": "http://calibre-web:8083",
        "mode": "forward_single",
        "intercept_header_auth": True
    }
    resp = requests.post(f"{AUTHENTIK_URL}/api/v3/providers/proxy/", headers=HEADERS, json=data)
    if resp.status_code >= 400:
        print(f"Error creating provider: {resp.text}")
    resp.raise_for_status()
    print("Created Provider")
    return resp.json()['pk']

def get_app_slug(provider_pk):
    """Get existing or create new Application."""
    # Check if exists
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/core/applications/", headers=HEADERS, params={"search": "Calibre Web"})
    resp.raise_for_status()
    results = resp.json().get("results", [])
    
    if results:
        # Check if provider is correct
        if results[0].get("provider") != provider_pk:
             # Update provider
             print("Updating application provider link...")
             requests.patch(f"{AUTHENTIK_URL}/api/v3/core/applications/{results[0]['slug']}/", headers=HEADERS, json={"provider": provider_pk})
        print(f"Application already exists: {results[0]['slug']}")
        return results[0]['slug']
    
    # Create
    data = {
        "name": "Calibre Web",
        "slug": "calibre-web",
        "provider": provider_pk
    }
    resp = requests.post(f"{AUTHENTIK_URL}/api/v3/core/applications/", headers=HEADERS, json=data)
    if resp.status_code >= 400:
        print(f"Error creating application: {resp.text}")
    resp.raise_for_status()
    print("Created Application")
    return resp.json()['slug']

def configure_outpost(provider_pk):
    """Add provider to embedded outpost."""
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/outposts/instances/", headers=HEADERS, params={"search": "authentik Embedded Outpost"})
    resp.raise_for_status()
    results = resp.json().get("results", [])
    
    if not results:
        print("ERROR: Embedded Outpost not found!")
        return
    
    outpost = results[0]
    outpost_pk = outpost['pk']
    current_providers = outpost.get('providers', [])
    
    if provider_pk not in current_providers:
        print(f"Adding provider {provider_pk} to outpost {outpost_pk}...")
        current_providers.append(provider_pk)
        data = {"providers": current_providers}
        resp = requests.patch(f"{AUTHENTIK_URL}/api/v3/outposts/instances/{outpost_pk}/", headers=HEADERS, json=data)
        if resp.status_code >= 400:
            print(f"Error updating outpost: {resp.text}")
        resp.raise_for_status()
        print("Outpost updated.")
    else:
        print("Provider already in outpost.")

def main():
    try:
        print("Starting configuration...")
        provider_pk = get_provider_pk()
        get_app_slug(provider_pk)
        configure_outpost(provider_pk)
        print("\n✅ Configuration Complete!")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
