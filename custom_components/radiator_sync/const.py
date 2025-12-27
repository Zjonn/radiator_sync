DOMAIN = "radiator_sync"

# Device + heater
CONF_HEATER = "heater"
CONF_MIN_ON = "min_on_s"
CONF_MIN_OFF = "min_off_s"

# Rooms structure
CONF_ROOMS = "rooms"
CONF_NAME = "room_name"
CONF_ROOM_CLIMATE = "climate_entity"
CONF_SENSOR_TEMP = "temperature_sensor"
CONF_SENSOR_HUM = "humidity_sensor"
CONF_HYSTERESIS = "hysteresis"
CONF_PRESETS = "presets"

# Defaults
DEFAULT_HYSTERESIS = 0.3
DEFAULT_MIN_ON = 8 * 60
DEFAULT_MIN_OFF = 5 * 60

DEFAULT_PRESETS = {
    "Night": 19.5,
    "Away": 15.0,
}
