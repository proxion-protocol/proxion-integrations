
import requests

AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def update_global_config():
    # Update external_host
    # Authentik system config is at /api/v3/core/config/
    # But usually we set it on the Brand or the Outpost?
    # Actually, the 'external_host' is a global property.
    
    # Let's try to PATCH it.
    data = {
        "external_host": "http://localhost:9000"
    }
    resp = requests.patch(f"{AUTHENTIK_URL}/api/v3/core/config/", headers=HEADERS, json=data)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("Successfully updated external_host.")
    else:
        print(f"Error: {resp.text}")

if __name__ == "__main__":
    update_global_config()
