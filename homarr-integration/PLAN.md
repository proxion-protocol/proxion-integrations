# Implementation Plan: Homarr Unified Dashboard

## Goal
Deploy a central, beautiful dashboard at `localhost:3003` that provides a single point of entry and monitoring for the entire Proxion Suite.

## Proposed Changes

### [Component] Homarr Integration
#### [NEW] [docker-compose.yml](file:///c:/Users/hobo/Desktop/Proxion/integrations/homarr-integration/docker-compose.yml)
*   **Image**: `ghcr.io/ajnart/homarr:latest`
*   **Persistent Storage**: Maps `P:/system/dashboard/configs` and `P:/system/dashboard/icons`.
*   **Port**: `3003:7575`

#### [NEW] [config_generator.py](file:///c:/Users/hobo/Desktop/Proxion/integrations/homarr-integration/generate_config.py)
*   **Function**: Reads `dashboard/src/data/apps.json` and produces a `default.json` for Homarr.
*   **Widget Logic**: Automatically maps service names and ports. Adds standard Monitoring widgets (HTTP checks).

### [Component] Expansion Widgets
#### [NEW] [dashdot-integration](file:///c:/Users/hobo/Desktop/Proxion/integrations/dashdot-integration/)
*   **Image**: `mauricenino/dashdot`
*   **Storage**: `P:/system/stats`
*   **Function**: Provides the system health data for the Homarr "DashDot" widget.

#### [NEW] [overseerr-integration](file:///c:/Users/hobo/Desktop/Proxion/integrations/overseerr-integration/)
*   **Storage**: `P:/media/requests`

#### [NEW] [tautulli-integration](file:///c:/Users/hobo/Desktop/Proxion/integrations/tautulli-integration/)
*   **Storage**: `P:/media/plex-stats`

## Verification Plan
1.  **Build**: Run `python generate_config.py`.
2.  **Deploy**: Run `proxion suite up homarr`.
3.  **Validate**: Access `http://localhost:3003` and verify all 30+ app icons are present and working.
