
import authentik_client
from authentik_client.api import core_api

AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "e8KWOC1MLtRFBLCWrOaquQhMX5abMWOkoy2uIuXjowndhJammbC9l5lWuz07"

config = authentik_client.Configuration(
    host=f"{AUTHENTIK_URL}/api/v3",
)
# config.api_key['Authorization'] = f"Bearer {API_TOKEN}"
# config.api_key_prefix['Authorization'] = "Bearer"

client = authentik_client.ApiClient(config)
client.default_headers['Authorization'] = f"Bearer {API_TOKEN}"
api = core_api.CoreApi(client)

try:
    user = api.core_users_me_retrieve()
    print(f"Success! User: {user.username}")
except Exception as e:
    print(f"Error: {e}")
