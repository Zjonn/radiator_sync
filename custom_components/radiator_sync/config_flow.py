import voluptuous as vol
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

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
    CONF_PRESETS,
    DEFAULT_PRESETS,
    CONF_MIN_ON,
    CONF_MIN_OFF,
    DEFAULT_MIN_ON,
    DEFAULT_MIN_OFF,
)


class RadiatorSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        """Initial step: choose heater entity and heater timings."""
        if user_input is not None:
            # Create entry with heater only; rooms are added via options flow
            data = {
                CONF_HEATER: user_input[CONF_HEATER],
                CONF_MIN_ON: user_input.get(CONF_MIN_ON, DEFAULT_MIN_ON),
                CONF_MIN_OFF: user_input.get(CONF_MIN_OFF, DEFAULT_MIN_OFF),
            }
            return self.async_create_entry(
                title="RadiatorSync",
                data=data,
                options={CONF_ROOMS: {}, CONF_PRESETS: DEFAULT_PRESETS},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HEATER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch"])
                ),
                vol.Optional(CONF_MIN_ON, default=DEFAULT_MIN_ON): int,  # type: ignore
                vol.Optional(CONF_MIN_OFF, default=DEFAULT_MIN_OFF): int,  # type: ignore
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
        
        # Normalize presets from old format if needed
        raw_presets = entry.options.get(CONF_PRESETS, DEFAULT_PRESETS)
        self.presets: Dict[str, Any] = {}
        for name, val in raw_presets.items():
            if isinstance(val, (int, float)):
                self.presets[name] = {"default": float(val), "overrides": {}}
            else:
                self.presets[name] = val

        self.room_name: str | None = None

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input["operation"]

            if action == "add_room":
                return await self.async_step_add_room()
            if action == "edit_room":
                return await self.async_step_edit_room()
            if action == "remove_room":
                return await self.async_step_remove_room()
            if action == "manage_presets":
                return await self.async_step_manage_presets()

        schema = vol.Schema(
            {
                vol.Required("operation"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "add_room", "label": "add_room"},
                            {"value": "edit_room", "label": "edit_room"},
                            {"value": "remove_room", "label": "remove_room"},
                            {"value": "manage_presets", "label": "manage_presets"},
                        ],
                        translation_key="operation",
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    # ---------- ADD ROOM ----------
    async def async_step_add_room(self, user_input=None):
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Optional(CONF_ROOM_CLIMATE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Required(CONF_SENSOR_TEMP): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SENSOR_HUM): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_HYSTERESIS, default=DEFAULT_HYSTERESIS): vol.Coerce(  # type: ignore
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
    async def async_step_edit_room(self, user_input=None):
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
        def _get_default(key, default_val: Any = vol.UNDEFINED):
            val = room.get(key)
            if val is None:
                return default_val
            return val

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=_get_default(CONF_NAME)): str,
                vol.Optional(
                    CONF_ROOM_CLIMATE, default=_get_default(CONF_ROOM_CLIMATE)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="climate")
                ),
                vol.Required(
                    CONF_SENSOR_TEMP, default=_get_default(CONF_SENSOR_TEMP)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_SENSOR_HUM, default=_get_default(CONF_SENSOR_HUM)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_HYSTERESIS,
                    default=_get_default(CONF_HYSTERESIS, DEFAULT_HYSTERESIS),
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(step_id="edit_room_apply", data_schema=schema)

    async def async_step_edit_room_apply(self, user_input=None):
        if self.room_name is None or user_input is None:
            return self.async_abort(reason="internal_error")

        old_room = self.rooms[self.room_name]
        new_name = user_input[CONF_NAME].strip()

        if new_name != self.room_name and new_name in self.rooms:
            return self._edit_room_form(old_room)

        self.rooms.pop(self.room_name)
        self.rooms[new_name] = {**old_room, **user_input}
        return await self._save_and_restart_options()

    # ---------- REMOVE ROOM ----------
    async def async_step_remove_room(self, user_input=None):
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

    # ---------- WRITE OPTIONS ----------
    async def _save_and_restart_options(self):
        return self.async_create_entry(
            title="", data={CONF_ROOMS: self.rooms, CONF_PRESETS: self.presets}
        )

    # ---------- MANAGE PRESETS ----------
    async def async_step_manage_presets(self, user_input=None):
        """Manage global presets."""
        if user_input is not None:
            action = user_input["preset_action"]
            if action == "add":
                return await self.async_step_add_preset()
            if action == "edit":
                return await self.async_step_edit_preset()
            if action == "remove":
                return await self.async_step_remove_preset()

        return self.async_show_form(
            step_id="manage_presets",
            data_schema=vol.Schema(
                {
                    vol.Required("preset_action"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["add", "edit", "remove"],
                            translation_key="preset_action",
                        )
                    )
                }
            ),
        )

    async def async_step_add_preset(self, user_input=None):
        """Add a new preset."""
        if user_input is not None:
            name = user_input["name"].strip()
            if name in self.presets:
                return self.async_show_form(
                    step_id="add_preset",
                    data_schema=self._get_preset_schema(),
                    errors={"name": "preset_exists"},
                )
            
            # Extract default and overrides
            default_temp = user_input["temperature"]
            overrides = {}
            for room_name in self.rooms:
                key = f"override_{room_name}"
                if key in user_input and user_input[key] is not None:
                    overrides[room_name] = user_input[key]
            
            self.presets[name] = {"default": default_temp, "overrides": overrides}
            return await self._save_and_restart_options()

        return self.async_show_form(
            step_id="add_preset", data_schema=self._get_preset_schema()
        )

    async def async_step_edit_preset(self, user_input=None):
        """Edit an existing preset."""
        if user_input is not None:
            if "name" in user_input and "temperature" not in user_input:
                # Selected name, now show temp + overrides
                name = user_input["name"]
                preset_data = self.presets.get(name, {"default": 21.0, "overrides": {}})
                return self.async_show_form(
                    step_id="edit_preset",
                    data_schema=self._get_preset_schema(
                        name, preset_data["default"], preset_data.get("overrides", {})
                    ),
                )
            
            # Saved temp + overrides
            name = user_input["name"]
            default_temp = user_input["temperature"]
            overrides = {}
            for room_name in self.rooms:
                key = f"override_{room_name}"
                if key in user_input and user_input[key] is not None:
                    overrides[room_name] = user_input[key]
            
            self.presets[name] = {"default": default_temp, "overrides": overrides}
            return await self._save_and_restart_options()

        return self.async_show_form(
            step_id="edit_preset",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=list(self.presets.keys()))
                    )
                }
            ),
        )

    async def async_step_remove_preset(self, user_input=None):
        """Remove a preset."""
        if user_input is not None:
            name = user_input["name"]
            self.presets.pop(name, None)
            return await self._save_and_restart_options()

        return self.async_show_form(
            step_id="remove_preset",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=list(self.presets.keys()))
                    )
                }
            ),
        )

    def _get_preset_schema(self, name: str = "", temp: float = 21.0, overrides: Dict[str, Any] | None = None):
        overrides = overrides or {}
        schema_dict: Dict[Any, Any] = {
            vol.Required("name", default=name): str,
            vol.Required("temperature", default=temp): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5, max=30, step=0.5, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
        for room_name in self.rooms:
            # Add optional overrides for each room
            schema_dict[vol.Optional(f"override_{room_name}", default=overrides.get(room_name))] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5, max=30, step=0.5, mode=selector.NumberSelectorMode.BOX
                )
            )
        return vol.Schema(schema_dict)

    async def _delete_room_entities(self, room_name: str) -> None:
        er_reg = er.async_get(self.hass)
        entry_id = self.entry.entry_id

        for entity_id in list(er_reg.entities):
            ent = er_reg.entities[entity_id]
            if ent.config_entry_id == entry_id and room_name in ent.unique_id:
                er_reg.async_remove(entity_id)
