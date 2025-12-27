# Radiator Sync

[![codecov](https://codecov.io/gh/zjonn/radiator_sync/graph/badge.svg?token=ORB0M1Z2U4)](https://codecov.io/gh/zjonn/radiator_sync)

<p align="center">
  <img src="assets/logo.png" alt="Radiator Sync logo" width="240">
</p>

Home Assistant integration that synchronizes a central heater with room thermostats and temperature sensors.

## Features
- **Central Heater Control**: Manages a boiler or heater switch with configurable anti short-cycle timers.
- **Dynamic Room Management**: Add, edit, or remove rooms via an intuitive options flow.
- **Thermostat Synchronization**: Automatically boosts or reduces linked climate entity temperatures based on room temperature and hysteresis.
- **Helper Entities**:
    - **Room**: Binary sensor for heat demand, sensor for target temperature.
    - **Heater**: Select for override mode, number for demand threshold, and sensor for runtime statistics.
- **Fully Configurable**: Entirely driven by config flow and options flow; no YAML required.

## Installation via HACS
1. Add this repository to HACS as an Integration (Custom repositories -> URL -> Integration). Use your fork URL, e.g. `https://github.com/zjonn/radiator_sync`.
2. Install **Radiator Sync** from the HACS Integrations tab.
3. Restart Home Assistant.

## Manual installation
Copy `custom_components/radiator_sync` into your Home Assistant `config/custom_components` directory and restart Home Assistant.

## Configuration
1. In Home Assistant, go to **Settings > Devices & Services > Add Integration** and search for **Radiator Sync**.
2. **Initial Setup**: Pick the switch entity that controls your boiler/heater and set the minimum ON and OFF times (in seconds).
3. **Adding Rooms**: After the initial setup, click **Configure** (or Options) on the Radiator Sync integration card.
4. Select **add_room** and provide:
    - **Name**: A unique name for the room.
    - **Climate Entity**: The thermostat or radiator valve to control.
    - **Temperature Sensor**: The primary sensor for room temperature.
    - **Humidity Sensor** (Optional): A sensor for room humidity tracking.
    - **Hysteresis**: The temperature window for triggering heat demand (default: 0.3°C).

## Development container
- Requires Docker, VS Code and the Dev Containers extension.
- Open the repository folder in VS Code and run **Dev Containers: Reopen in Container**.
- The devcontainer image is `ghcr.io/home-assistant/devcontainer:stable` with port 8123 forwarded.
- The custom component is symlinked into `/config/custom_components/radiator_sync` inside the container.
- Start Home Assistant with `hass -c /config` (first run will create a default config).

## Notes
- Update `manifest.json` version and create a release when publishing new builds for HACS.
- Issue tracker and documentation are located at `https://github.com/zjonn/radiator_sync`.
