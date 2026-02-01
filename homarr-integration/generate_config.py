import json
import os
import uuid

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
APPS_JSON = os.path.join(BASE_DIR, "proxion-keyring/dashboard/src/data/apps.json")
OUTPUT_CONFIG = os.path.join(BASE_DIR, "integrations/homarr-integration/default.json")

def generate_config():
    if not os.path.exists(APPS_JSON):
        print(f"Error: {APPS_JSON} not found.")
        return

    with open(APPS_JSON, 'r') as f:
        apps = json.load(f)

    # Base Homarr Schema (Simplified for 0.15+)
    config = {
        "meta": {
            "name": "Proxion Private Suite"
        },
        "services": [],
        "widgets": [
            {
                "id": str(uuid.uuid4()),
                "type": "dashdot",
                "properties": {
                    "url": "http://localhost:3001"
                },
                "area": { "w": 6, "h": 4, "x": 0, "y": 0 }
            },
            {
                "id": str(uuid.uuid4()),
                "type": "clock",
                "properties": { "timezone": "UTC", "format": "HH:mm" },
                "area": { "w": 2, "h": 2, "x": 6, "y": 0 }
            }
        ]
    }

    # Map Categories to Y offsets to create sections
    category_map = {}
    y_offset = 5
    
    for app in apps:
        if app['id'] == 'homarr-integration': continue # Don't add dashboard to itself
        
        category = app.get('category', 'General')
        if category not in category_map:
            category_map[category] = y_offset
            y_offset += 3
        
        # Determine Icon (using jsdelivr collection as fallback)
        icon_slug = app['id'].replace("-integration", "").lower()
        icon_url = f"https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/{icon_slug}.png"
        
        service = {
            "id": str(uuid.uuid4()),
            "name": app['name'],
            "href": f"http://localhost:{app['port']}",
            "icon": icon_url,
            "category": category,
            "area": {
                "w": 1,
                "h": 1,
                "x": len([s for s in config['services'] if s['category'] == category]) % 8,
                "y": category_map[category]
            }
        }
        config['services'].append(service)

    # Save Config
    os.makedirs(os.path.dirname(OUTPUT_CONFIG), exist_ok=True)
    with open(OUTPUT_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Successfully generated Homarr config at {OUTPUT_CONFIG}")

if __name__ == "__main__":
    generate_config()
