import secrets
import os

def generate_key():
    return secrets.token_urlsafe(50)

def main():
    if os.path.exists(".env"):
        print("Authentik .env already exists. Skipping generation.")
        return

    pg_pass = generate_key()
    secret_key = generate_key()

    env_content = f"""# Authentik Configuration
PG_PASS={pg_pass}
AUTHENTIK_SECRET_KEY={secret_key}
AUTHENTIK_ERROR_REPORTING__ENABLED=false
AUTHENTIK_DISABLE_STARTUP_ANALYTICS=true
AUTHENTIK_DISABLE_UPDATE_CHECK=true

# Ports
COMPOSE_PORT_HTTP=9000
COMPOSE_PORT_HTTPS=9443

# Email (Optional - needed for password recovery, but we are using Sovereign keys)
# AUTHENTIK_EMAIL__HOST=localhost
# AUTHENTIK_EMAIL__PORT=25
# AUTHENTIK_EMAIL__USERNAME=
# AUTHENTIK_EMAIL__PASSWORD=
# AUTHENTIK_EMAIL__USE_TLS=false
# AUTHENTIK_EMAIL__FROM=authentik@localhost
"""

    with open(".env", "w") as f:
        f.write(env_content)
    
    print("Generated .env for Authentik.")

if __name__ == "__main__":
    main()
