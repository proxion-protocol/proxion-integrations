import requests
import json
import uuid

# Configuration
AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def main():
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/flows/instances/", headers=HEADERS, params={"slug": "default-provider-authorization-implicit-consent"})
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            print(f"Flow ID: {results[0]['pk']}")
        else:
            print("Flow not found via slug. Listing all flows:")
            resp = requests.get(f"{AUTHENTIK_URL}/api/v3/flows/instances/", headers=HEADERS)
            for f in resp.json().get("results", []):
                print(f"{f['slug']}: {f['pk']}")
    else:
        print(f"Error: {resp.text}")

if __name__ == "__main__":
    main()
