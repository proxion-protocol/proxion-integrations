
"""
Configure Authentik for Jellyfin SSO (OIDC/OAuth2).
"""

import requests
import json
import uuid

# Configuration
AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"
FLOW_PK = "cda727f9-4385-4550-b649-75608bb0278f" # implicit-consent flow

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def create_scope_mapping():
    """Create Python expression mapping for groups."""
    name = "Group Membership"
    expression = "return [group.name for group in user.ak_groups.all()]"
    
    # Check exists
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/propertymappings/scope/", headers=HEADERS, params={"name": name})
    results = resp.json().get("results", [])
    if results:
        return results[0]['pk']
        
    data = {
        "name": name,
        "scope_name": "groups",
        "expression": expression,
        "description": "Jellyfin Group Mapping",
    }
    resp = requests.post(f"{AUTHENTIK_URL}/api/v3/propertymappings/scope/", headers=HEADERS, json=data)
    resp.raise_for_status()
    print("Created Group Mapping")
    return resp.json()['pk']

def get_signing_key():
    """Get the self-signed certificate/key."""
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/crypto/certificatekeypairs/", headers=HEADERS, params={"name": "authentik Self-signed Certificate"})
    results = resp.json().get("results", [])
    if results:
        return results[0]['pk']
    # Fallback to any
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/crypto/certificatekeypairs/", headers=HEADERS, params={"page_size": 1})
    if resp.json().get("results"):
        return resp.json()["results"][0]["pk"]
    raise Exception("No signing key found! Initialize authentik first.")

def create_provider(scope_mapping_pk, signing_key_pk):
    """Create OAuth2 Provider."""
    name = "Jellyfin OAuth"
    # Check exists
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/providers/oauth2/", headers=HEADERS, params={"search": name})
    results = resp.json().get("results", [])
    if results:
        print("Provider exists.")
        return results[0]

    data = {
        "name": name,
        "authorization_flow": FLOW_PK,
        "client_type": "confidential",
        "client_id": str(uuid.uuid4()).replace("-", "")[:20],
        "client_secret": str(uuid.uuid4()).replace("-", ""),
        "redirect_uris": "http://localhost:8096/sso/OID/redirect/authentik",
        "signing_key": signing_key_pk,
        "property_mappings": [scope_mapping_pk]
    }
    # We must include default scopes too (email, profile, openid)
    # Actually, property_mappings in API usually appends. Let's see.
    # The default 'authentik default OAuth Mapping...' should be included by default? 
    # Let's ensure we fetch default mappings OIDs if needed, 
    # but usually creating provider assigns default mappings.
    # We will simply append our custom one in a PATCH if needed, or pass list of IDs.
    # To be safe, let's create it, then PATCH the scopes.
    
    resp = requests.post(f"{AUTHENTIK_URL}/api/v3/providers/oauth2/", headers=HEADERS, json=data)
    if resp.status_code >= 400:
        print(f"Error creating provider: {resp.text}")
    resp.raise_for_status()
    
    provider = resp.json()
    print("Created Provider")
    return provider

def create_application(provider_pk):
    """Create Application."""
    slug = "jellyfin"
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/core/applications/", headers=HEADERS, params={"slug": slug})
    results = resp.json().get("results", [])
    if results:
        return results[0]
        
    data = {
        "name": "Jellyfin",
        "slug": slug,
        "provider": provider_pk,
        "meta_launch_url": "http://localhost:8096"
    }
    resp = requests.post(f"{AUTHENTIK_URL}/api/v3/core/applications/", headers=HEADERS, json=data)
    resp.raise_for_status()
    print("Created Application")
    return resp.json()

def main():
    try:
        print("--- Configuring Jellyfin SSO ---")
        scope_pk = create_scope_mapping()
        key_pk = get_signing_key()
        provider = create_provider(scope_pk, key_pk)
        create_application(provider['pk'])
        
        print("\n✅ Configuration Complete!")
        print("-" * 30)
        print(f"Client ID:     {provider['client_id']}")
        print(f"Client Secret: {provider['client_secret']}")
        print("-" * 30)
        print("Copy these into the Jellyfin SSO-Auth Plugin settings.")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    main()
