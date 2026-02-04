
import requests

url = "http://localhost:9000/api/v3/flows/instances/?slug=default-provider-authorization-implicit-consent"
token = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"
headers = {
    "Authorization": f"Bearer {token}"
}

try:
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(resp.json())
except Exception as e:
    print(f"Error: {e}")
