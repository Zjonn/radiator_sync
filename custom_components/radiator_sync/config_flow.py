from __future__ import annotations

import voluptuous as vol
from typing import Any, Dict, List

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.core import callback
from homeassistant.helpers import entity_registry
from homeassistant.helpers import device_registry

from .const import (
    DOMAIN,
    CONF_HEATER,
    CONF_ROOMS,
    CONF_NAME,
    CONF_ROOM_CLIMATE,
    CONF_SENSOR_TEMP,
    CONF_SENSOR_HUM,
    CONF_HYSTERESIS,
    DEFAULT_HYSTERESIS,
    CONF_MIN_ON,
    CONF_MIN_OFF,
    DEFAULT_MIN_ON,
    DEFAULT_MIN_OFF,
)


class RadiatorSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Initial step: choose heater entity and heater timings."""
        if user_input is not None:
            # Create entry with heater only; rooms are added via options flow
            data = {
                CONF_HEATER: user_input[CONF_HEATER],
                CONF_MIN_ON: user_input.get(CONF_MIN_ON, DEFAULT_MIN_ON),
                CONF_MIN_OFF: user_input.get(CONF_MIN_OFF, DEFAULT_MIN_OFF),
            }
            return self.async_create_entry(
                title="RadiatorSync", data=data, options={CONF_ROOMS: {}}
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HEATER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch"])
                ),
                vol.Optional(CONF_MIN_ON, default=DEFAULT_MIN_ON): int,
                vol.Optional(CONF_MIN_OFF, default=DEFAULT_MIN_OFF): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return RadiatorSyncOptionsFlow(config_entry)


class RadiatorSyncOptionsFlow(config_entries.OptionsFlow):
    """Handle options for RadiatorSync: add/edit/remove rooms."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry
        self.rooms: Dict[str, Dict[str, Any]] = dict(entry.options.get(CONF_ROOMS, {}))
        self.room_name: str | None = None

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            action = user_input["operation"]

            if action == "add_room":
                return await self.async_step_add_room()
            if action == "edit_room":
                return await self.async_step_edit_room()
            if action == "remove_room":
                return await self.async_step_remove_room()
            if action == "finish":
                return await self.async_step_finish()

        schema = vol.Schema(
            {
                vol.Required("operation"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "add_room", "label": "add_room"},
                            {"value": "edit_room", "label": "edit_room"},
                            {"value": "remove_room", "label": "remove_room"},
                            {"value": "finish", "label": "finish"},
                        ], 
                        translation_key="operation"
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    # ---------- ADD ROOM ----------
    async def async_step_add_room(self, user_input=None) -> FlowResult:
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_ROOM_CLIMATE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Required(CONF_SENSOR_TEMP): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SENSOR_HUM): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_HYSTERESIS, default=DEFAULT_HYSTERESIS): vol.Coerce(
                    float
                ),
            }
        )

        if user_input is not None:
            name = user_input[CONF_NAME].strip()

            if name in self.rooms:
                return self.async_show_form(
                    step_id="add_room",
                    data_schema=schema,
                    errors={"base": "name_exists"},
                )

            self.rooms[name] = user_input
            return await self._save_and_restart_options()

        return self.async_show_form(step_id="add_room", data_schema=schema)

    # ---------- EDIT ROOM ----------
    async def async_step_edit_room(self, user_input=None) -> FlowResult:
        if not self.rooms:
            return self.async_abort(reason="no_rooms")

        if user_input is not None and "name" in user_input:
            name = user_input["name"]
            self.room_name = name
            room = self.rooms[name]

            return self._edit_room_form(room)

        schema = vol.Schema(
            {
                vol.Required("name"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=list(self.rooms.keys()))
                )
            }
        )
        return self.async_show_form(step_id="edit_room", data_schema=schema)

    def _edit_room_form(self, room):
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=room.get(CONF_NAME)): str,
                vol.Required(
                    CONF_ROOM_CLIMATE, default=room.get(CONF_ROOM_CLIMATE)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Required(
                    CONF_SENSOR_TEMP, default=room.get(CONF_SENSOR_TEMP)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_SENSOR_HUM, default=room.get(CONF_SENSOR_HUM)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_HYSTERESIS,
                    default=room.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS),
                ): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="edit_room_apply", data_schema=schema)

    async def async_step_edit_room_apply(self, user_input=None) -> FlowResult:
        if self.room_name is None:
            return self.async_abort(reason="internal_error")

        old_room = self.rooms[self.room_name]
        new_name = user_input[CONF_NAME].strip()

        if new_name != self.room_name and new_name in self.rooms:
            return self._edit_room_form(old_room)

        self.rooms.pop(self.room_name)
        self.rooms[new_name] = {**old_room, **user_input}
        return await self._save_and_restart_options()

    # ---------- REMOVE ROOM ----------
    async def async_step_remove_room(self, user_input=None) -> FlowResult:
        if not self.rooms:
            return self.async_abort(reason="no_rooms")

        if user_input is not None and "name" in user_input:
            name = user_input["name"]
            self.rooms.pop(name)
            await self._delete_room_entities(name)
            return await self._save_and_restart_options()

        schema = vol.Schema(
            {
                vol.Required("name"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=list(self.rooms.keys()))
                )
            }
        )
        return self.async_show_form(step_id="remove_room", data_schema=schema)

    # ---------- FINISH ----------
    async def async_step_finish(self, user_input=None) -> FlowResult:
        return await self._save_and_restart_options()

    # ---------- WRITE OPTIONS ----------
    async def _save_and_restart_options(self) -> FlowResult:
        return self.async_create_entry(title="", data={CONF_ROOMS: self.rooms})
