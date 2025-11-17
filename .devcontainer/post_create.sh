#!/usr/bin/env bash
set -euo pipefail

# Runs inside the devcontainer with the workspace mounted at $PWD
ROOT_DIR="$(pwd)"
HA_CONFIG="/config"
COMPONENT_NAME="radiator_sync"
SRC_PATH="${ROOT_DIR}/custom_components/${COMPONENT_NAME}"
DEST_PATH="${HA_CONFIG}/custom_components/${COMPONENT_NAME}"

mkdir -p "${HA_CONFIG}/custom_components"

# Link the component into the Home Assistant config for live development
if [ -e "${DEST_PATH}" ] && [ ! -L "${DEST_PATH}" ]; then
  echo "Warning: ${DEST_PATH} exists and is not a symlink; skipping link."
else
  ln -sfn "${SRC_PATH}" "${DEST_PATH}"
fi

echo "Devcontainer ready. Start Home Assistant with: hass -c /config"
