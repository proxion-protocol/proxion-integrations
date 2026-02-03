"""
Configure Authentik for Calibre-Web SSO

Uses the official authentik-client library.
Requires: pip install authentik-client
"""

import authentik_client
from authentik_client.api import core_api, providers_api, flows_api, outposts_api
from authentik_client.models import (
    ProxyProviderRequest,
    ApplicationRequest,
    ServiceConnectionRequest,
    OutpostRequest,
    ProxyMode,
)

# Configuration - Update this token!
AUTHENTIK_URL = "http://localhost:9000"
API_TOKEN = "YOUR_TOKEN_HERE"  # Create in Admin UI: Directory -> Tokens & App Passwords

def get_client():
    """Create configured API client."""
    config = authentik_client.Configuration(
        host=f"{AUTHENTIK_URL}/api/v3",
    )
    config.api_key["Authorization"] = API_TOKEN
    config.api_key_prefix["Authorization"] = "Bearer"
    return authentik_client.ApiClient(config)

def get_authorization_flow(api_client):
    """Find the implicit consent flow."""
    flows = flows_api.FlowsApi(api_client)
    try:
        # Try implicit first (no "Authorize" button for user)
        result = flows.flows_instances_list(slug="default-provider-authorization-implicit-consent")
        if result.results:
            return result.results[0].pk
    except Exception:
        pass
    
    # Fallback to explicit
    result = flows.flows_instances_list(slug="default-provider-authorization-explicit-consent")
    if result.results:
        return result.results[0].pk
    
    raise Exception("No authorization flow found")

def create_provider(api_client, auth_flow_pk):
    """Create the Proxy Provider for Calibre."""
    providers = providers_api.ProvidersApi(api_client)
    
    # Check if exists
    existing = providers.providers_proxy_list(name="Calibre Provider")
    if existing.results:
        print(f"Provider already exists: {existing.results[0].pk}")
        return existing.results[0].pk
    
    # Create new
    request = ProxyProviderRequest(
        name="Calibre Provider",
        authorization_flow=auth_flow_pk,
        external_host="http://localhost:8083",
        internal_host="http://calibre-web:8083",
        mode=ProxyMode.FORWARD_SINGLE,
        intercept_header_auth=True,
    )
    result = providers.providers_proxy_create(proxy_provider_request=request)
    print(f"Created Provider: {result.pk}")
    return result.pk

def create_application(api_client, provider_pk):
    """Create the Application for Calibre."""
    apps = core_api.CoreApi(api_client)
    
    # Check if exists
    existing = apps.core_applications_list(name="Calibre Web")
    if existing.results:
        print(f"Application already exists: {existing.results[0].slug}")
        return existing.results[0].slug
    
    # Create new
    request = ApplicationRequest(
        name="Calibre Web",
        slug="calibre-web",
        provider=provider_pk,
    )
    result = apps.core_applications_create(application_request=request)
    print(f"Created Application: {result.slug}")
    return result.slug

def get_or_create_outpost(api_client, provider_pk):
    """Get or create the embedded outpost for the proxy."""
    outposts = outposts_api.OutpostsApi(api_client)
    
    # Check for existing embedded outpost
    existing = outposts.outposts_instances_list(name="authentik Embedded Outpost")
    if existing.results:
        outpost = existing.results[0]
        # Add our provider to it
        current_providers = outpost.providers or []
        if provider_pk not in current_providers:
            current_providers.append(provider_pk)
            outposts.outposts_instances_partial_update(
                uuid=outpost.pk,
                patched_outpost_request={"providers": current_providers}
            )
            print(f"Added provider to existing outpost")
        return outpost.pk
    
    print("No embedded outpost found. You may need to create one in the UI.")
    return None

def main():
    if API_TOKEN == "YOUR_TOKEN_HERE":
        print("ERROR: Please set API_TOKEN first!")
        print("Steps:")
        print("1. Go to http://localhost:9000/if/admin/")
        print("2. Directory -> Tokens & App Passwords")
        print("3. Create a new token for 'akadmin'")
        print("4. Copy the token key and paste it in this script")
        return
    
    with get_client() as client:
        # 1. Get flow
        auth_flow = get_authorization_flow(client)
        print(f"Using flow: {auth_flow}")
        
        # 2. Create Provider
        provider_pk = create_provider(client, auth_flow)
        
        # 3. Create Application
        app_slug = create_application(client, provider_pk)
        
        # 4. Configure Outpost
        get_or_create_outpost(client, provider_pk)
        
        print("\n✅ DONE! Calibre Web is now configured in Authentik.")
        print(f"   Access via: http://localhost:9000/if/user/#/applications")

if __name__ == "__main__":
    main()
