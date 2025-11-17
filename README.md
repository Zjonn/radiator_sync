# Radiator Sync

Home Assistant integration that synchronizes a central heater with room thermostats and temperature sensors.

## Features
- Config entry for boiler switch with anti short-cycle timers.
- Options flow to manage rooms with target temperatures, hysteresis and optional humidity sensors.
- Automatically boosts or reduces the linked climate entity temperature to keep rooms within the hysteresis window.
- Exposes helper entities (binary_sensor, select, number, sensor) for override mode, demand threshold and runtime statistics.
- Fully config-flow driven; no YAML required.

## Installation via HACS
1. Add this repository to HACS as an Integration (Custom repositories -> URL -> Integration). Use your fork URL, e.g. `https://github.com/zjonn/radiator_sync`.
2. Install Radiator Sync from the HACS Integrations tab.
3. Restart Home Assistant.

## Manual installation
Copy `custom_components/radiator_sync` into your Home Assistant `config/custom_components` directory and restart Home Assistant.

## Configuration
1. In Home Assistant, go to **Settings > Devices & Services > Add Integration** and search for **Radiator Sync**.
2. Pick the switch entity that controls your boiler/heater and optionally adjust the minimum on/off times (seconds).
3. Open the integration options to add rooms: name, room climate entity, temperature sensor, optional humidity sensor and hysteresis.
4. Each room exposes entities for heat demand and target temperature; the heater exposes runtime and override controls.

## Development container
- Requires Docker, VS Code and the Dev Containers extension.
- Open the repository folder in VS Code and run **Dev Containers: Reopen in Container**.
- The devcontainer image is `ghcr.io/home-assistant/devcontainer:stable` with port 8123 forwarded.
- The custom component is symlinked into `/config/custom_components/radiator_sync` inside the container.
- Start Home Assistant with `hass -c /config` (first run will create a default config).

## Notes
- Update `manifest.json` version and create a release when publishing new builds for HACS.
- Issue tracker and documentation are assumed to live at `https://github.com/zjonn/radiator_sync`; adjust if your remote differs.
