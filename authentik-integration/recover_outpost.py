
import requests
import json
import os

AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "bpWg7k5dl1g10E4zxdwIsz7j5pmLzjRFvOoBmeuHPMxzcSkIFXJI8b6Y2ayg"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def main():
    print("--- Recovering Embedded Outpost ---")
    
    # 1. Find Calibre Provider
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/providers/proxy/", headers=HEADERS, params={"search": "Calibre"})
    results = resp.json().get("results", [])
    if not results:
        print("❌ Calibre Provider not found!")
        return
    provider = results[0]
    provider_pk = provider['pk']
    print(f"✅ Found Provider: {provider['name']} (pk={provider_pk})")

    # 2. Check for existing (double check)
    resp = requests.get(f"{AUTHENTIK_URL}/api/v3/outposts/instances/", headers=HEADERS)
    outposts = resp.json().get("results", [])
    if outposts:
        print("Outpost found during recovery? Aborting creation.")
        return

    # 3. Create Outpost
    print("Creating 'authentik Embedded Outpost'...")
    
    # We need a Service Connection. Usually auto-created.
    # Let's try creating without specifying checking if it auto-assigns.
    
    data = {
        "name": "authentik Embedded Outpost",
        "type": "proxy",
        "providers": [provider_pk],
        "service_connection": None, # Local
        "config": {
             "authentik_host": "http://authentik-integration-server-1:9000",
             "authentik_host_insecure": False,
             "authentik_host_browser": "",
             "log_level": "debug",
             "object_naming_template": "ak-outpost-%(name)s",
             "docker_network": "proxion-sso",
             "docker_map_ports": True,
             "docker_labels": None,
             "container_image": None,
             "kubernetes_replicas": 1,
             "kubernetes_namespace": "default"
        }
    }
    
    # Try creating. If it fails on Service Connection, we might need to find the "Local" one.
    resp = requests.post(f"{AUTHENTIK_URL}/api/v3/outposts/instances/", headers=HEADERS, json=data)
    
    if resp.status_code >= 400:
        print(f"❌ Creation Failed: {resp.text}")
    else:
        print("✅ Outpost Created Successfully!")
        print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    main()
