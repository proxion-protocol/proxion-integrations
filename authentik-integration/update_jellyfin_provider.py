
import requests

# Configuration
AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def update_provider():
    # 1. Find the provider
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/providers/oauth2/", headers=HEADERS, params={"search": "Jellyfin OAuth"})
    results = resp.json().get("results", [])
    if not results:
        print("Provider not found")
        return
    
    provider = results[0]
    pk = provider['pk']
    
    # 2. Update Redirect URIs to include capitalization variant just in case
    # The doc says: https://domain.tld/sso/OID/redirect/Authentik
    # We are using http://localhost:8096/sso/OID/redirect/authentik
    # Let's add BOTH.
    redirect_uris = "http://localhost:8096/sso/OID/redirect/authentik\nhttp://localhost:8096/sso/OID/redirect/Authentik"
    
    print(f"Updating Provider {pk}...")
    data = {
        "redirect_uris": redirect_uris
    }
    resp = requests.patch(f"{AUTHENTIK_URL}/api/v3/providers/oauth2/{pk}/", headers=HEADERS, json=data)
    if resp.status_code >= 400:
        print(f"Error: {resp.text}")
    resp.raise_for_status()
    print("Success: Redirect URIs updated.")

if __name__ == "__main__":
    update_provider()
