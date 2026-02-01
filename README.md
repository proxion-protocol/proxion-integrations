# Proxion Integrations: The 90-App Library 📦🏛️

This repository contains the definitive library of containerized application environments for the **Proxion Suite**. It enables a world-class, private alternative to every major cloud service.

## 🏗️ Architecture: The Integration Principle
Proxion Integrations are not just simple Docker Compose files. They are highly-refined, pre-configured environments designed for:

1.  **Stateless Execution**: All persistent data is mapped to subfolders of the **Proxion Drive (P:)**.
2.  **Zero-Trust Identity**: Protected by **Authelia** for SSO/2FA and the **Resource Server** for capability-based access.
3.  **Network Isolation**: All apps run on the internal `proxion-network` with minimal exposure to the host.
4.  **Automatic Provisioning**: Every integration includes a `start_*.py` or `docker-compose.override.yml` to automate the heavy lifting of initialization.

## 📂 The Library (90+ Applications)

### 📁 Core Suite
- **Auth**: Authelia (SSO/2FA).
- **Management**: Homarr (Dashboard), Portainer (Docker GUI).
- **Infrastructure**: Proxion Keyring, Watchtower, Uptime Kuma.

### 📁 Productivity & Finance
- **Notes & Work**: Joplin, VS Code (Sync), Vikunja, CryptPad.
- **Finance**: Actual Budget, Ghostfolio, Wallos.
- **Documents**: Paperless-ngx, Stirling-PDF, SilverBullet.

### 📁 Social & Communication
- **Federated**: Bluesky PDS (ATProtocol), Mastodon, Lemmy, Pixelfed.
- **Real-time**: Matrix (Synapse), Jitsi Meet, Mattermost.
- **Personal**: Monica (PRM).

### 📁 Media & Entertainment
- **The "Arrs"**: Sonarr, Radarr, Lidarr, Prowlarr, Readarr, Bazarr.
- **Streaming**: Jellyfin, Plex, Navidrome, Audiobookshelf, Kavita.
- **Gaming**: Steam Headless, Pterodactyl, RomM, EmulatorJS.

### 📁 Home & Security
- **Automation**: Home Assistant, Homebridge, PiAlert.
- **Privacy**: Pi-hole, AdGuard Home, SearXNG.
- **Backups**: Kopia, Syncthing.

## 🚀 Usage (Development)
These integrations are orchestrated by the [proxion-keyring](file:///c:/Users/hobo/Desktop/Proxion/proxion-keyring) CLI. 

To manually test an integration:
```bash
cd integrations/immich-integration
docker-compose up -d
```

## 🛡️ Security
Every integration is audited for data isolation. No application stores state internally; all state is anchored to your portable Identity Key via Drive P:.
