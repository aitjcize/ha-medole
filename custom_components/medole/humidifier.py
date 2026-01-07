"""Humidifier platform for Medole Dehumidifier integration."""

import logging
from datetime import timedelta

from homeassistant.components.humidifier import (
    HumidifierAction,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONTINUOUS_DEHUMIDIFICATION,
    DOMAIN,
    FAN_SPEED_HIGH,
    MAX_HUMIDITY,
    MIN_HUMIDITY,
    REG_DEHUMIDIFY_MODE,
    REG_FAN_SPEED,
    REG_HUMIDITY_1,
    REG_HUMIDITY_SETPOINT,
    REG_OPERATION_STATUS,
    REG_POWER,
    REG_PURIFY_MODE,
    STATUS_COMPRESSOR_ON,
    STATUS_FAN_ON,
)

# No need to import modbus functions as we'll use the client methods directly

_LOGGER = logging.getLogger(__name__)

# Polling interval
SCAN_INTERVAL = timedelta(seconds=5)

# Preset modes
PRESET_MODE_DEHUMIDIFY = "Dehumidify"
PRESET_MODE_AIR_PURIFICATION = "Air Purification"
PRESET_MODES = [PRESET_MODE_DEHUMIDIFY, PRESET_MODE_AIR_PURIFICATION]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Medole Dehumidifier humidifier platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    config = data["config"]
    client = data["client"]

    name = config[CONF_NAME]

    async_add_entities(
        [MedoleDehumidifierHumidifier(hass, name, client)],
        True,
    )


class MedoleDehumidifierHumidifier(HumidifierEntity):
    """Representation of a Medole Dehumidifier humidifier device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_device_class = HumidifierDeviceClass.DEHUMIDIFIER
    _attr_available_modes = PRESET_MODES
    _attr_min_humidity = MIN_HUMIDITY
    _attr_max_humidity = MAX_HUMIDITY

    def __init__(self, hass, name, client):
        """Initialize the humidifier device."""
        self.hass = hass
        self._client = client
        self._attr_unique_id = f"{name}_humidifier"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": name,
            "manufacturer": "Medole",
            "model": "IN-D17",
        }

        # Initialize state variables
        self._attr_current_humidity = None
        self._attr_target_humidity = None
        self._attr_mode = None
        self._attr_is_on = False
        self._attr_action = None
        self._current_preset = PRESET_MODE_DEHUMIDIFY

    @property
    def current_humidity(self):
        """Return current humidity to set with the ring."""
        return self._attr_current_humidity

    @property
    def target_humidity(self):
        """Return target humidity to set with the ring."""
        return self._attr_target_humidity

    @property
    def min_humidity(self):
        """Return minimum humidity settable with the ring."""
        return self._attr_min_humidity

    @property
    def max_humidity(self):
        """Return maximum humidity settable with the ring."""
        return self._attr_max_humidity

    async def async_update(self) -> None:
        """Update the state of the humidifier device."""
        # Get power status
        power_result = await self._client.async_read_register(REG_POWER)
        if power_result:
            power_status = power_result.registers[0]
            self._attr_is_on = power_status == 1
        else:
            _LOGGER.error("Failed to read power status")
            return

        # Get the operation status register
        status_result = await self._client.async_read_register(
            REG_OPERATION_STATUS
        )

        if status_result:
            status = status_result.registers[0]
            compressor_on = status & STATUS_COMPRESSOR_ON
            fan_on = status & STATUS_FAN_ON

            # Determine action based on operation status
            if not self._attr_is_on:
                self._attr_action = HumidifierAction.OFF
            elif compressor_on:
                self._attr_action = HumidifierAction.DRYING
            elif fan_on:
                self._attr_action = HumidifierAction.IDLE
            else:
                self._attr_action = HumidifierAction.IDLE
        else:
            _LOGGER.error("Failed to read operation status")

        # Get the humidity setpoint
        setpoint_result = await self._client.async_read_register(
            REG_HUMIDITY_SETPOINT
        )

        if setpoint_result:
            humidity_setpoint = setpoint_result.registers[0]
            if humidity_setpoint == CONTINUOUS_DEHUMIDIFICATION:
                # For continuous mode, set to minimum
                self._attr_target_humidity = MIN_HUMIDITY
            else:
                self._attr_target_humidity = humidity_setpoint
        else:
            _LOGGER.error("Failed to read humidity setpoint")

        # Check which mode is active (dehumidify or air purification)
        dehumidify_result = await self._client.async_read_register(
            REG_DEHUMIDIFY_MODE
        )
        purify_result = await self._client.async_read_register(REG_PURIFY_MODE)

        if dehumidify_result and purify_result:
            dehumidify_on = dehumidify_result.registers[0] == 1
            purify_on = purify_result.registers[0] == 1

            # Prioritize showing dehumidify mode when both are active
            if dehumidify_on:
                self._current_preset = PRESET_MODE_DEHUMIDIFY
                self._attr_mode = PRESET_MODE_DEHUMIDIFY
            elif purify_on:
                self._current_preset = PRESET_MODE_AIR_PURIFICATION
                self._attr_mode = PRESET_MODE_AIR_PURIFICATION
            else:
                # Neither mode is active
                self._current_preset = PRESET_MODE_DEHUMIDIFY
                self._attr_mode = PRESET_MODE_DEHUMIDIFY

        # Get the current humidity
        humidity_result = await self._client.async_read_register(REG_HUMIDITY_1)

        if humidity_result:
            self._attr_current_humidity = humidity_result.registers[0]
        else:
            _LOGGER.error("Failed to read current humidity")

    async def async_set_mode(self, mode: str) -> None:
        """Set new mode."""
        if mode == PRESET_MODE_AIR_PURIFICATION:
            # Switch to air purification mode with high fan speed
            await self._client.async_write_register(
                REG_FAN_SPEED, FAN_SPEED_HIGH
            )
            await self._client.async_write_register(REG_DEHUMIDIFY_MODE, 0)
            success = await self._client.async_write_register(
                REG_PURIFY_MODE, 1
            )
            if success:
                self._current_preset = PRESET_MODE_AIR_PURIFICATION
                self._attr_mode = mode
                _LOGGER.info("Switched to air purification mode")
            else:
                _LOGGER.error("Failed to set air purification mode")
        elif mode == PRESET_MODE_DEHUMIDIFY:
            # Switch to dehumidify mode with high fan speed
            await self._client.async_write_register(
                REG_FAN_SPEED, FAN_SPEED_HIGH
            )
            # Enable both purify and dehumidify modes
            await self._client.async_write_register(REG_PURIFY_MODE, 1)
            success = await self._client.async_write_register(
                REG_DEHUMIDIFY_MODE, 1
            )
            if success:
                self._current_preset = PRESET_MODE_DEHUMIDIFY
                self._attr_mode = PRESET_MODE_DEHUMIDIFY
                _LOGGER.info("Switched to dehumidify mode")
            else:
                _LOGGER.error("Failed to set dehumidify mode")

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        # Ensure humidity is within valid range
        humidity = max(MIN_HUMIDITY, min(MAX_HUMIDITY, humidity))

        success = await self._client.async_write_register(
            REG_HUMIDITY_SETPOINT, humidity
        )

        if success:
            self._attr_target_humidity = humidity
        else:
            _LOGGER.error("Failed to set humidity to %s", humidity)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the device on."""
        # Set fan speed to high
        await self._client.async_write_register(REG_FAN_SPEED, FAN_SPEED_HIGH)

        # Set the power on
        result = await self._client.async_write_register(REG_POWER, 1)
        if not result:
            _LOGGER.error("Failed to turn on device")

        # Set dehumidify mode on
        result = await self._client.async_write_register(REG_DEHUMIDIFY_MODE, 1)
        if not result:
            _LOGGER.error("Failed to turn on dehumidify mode")

        # Set purify mode off
        result = await self._client.async_write_register(REG_PURIFY_MODE, 0)

        self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        # Set power off
        success = await self._client.async_write_register(REG_POWER, 0)

        if success:
            self._attr_is_on = False
        else:
            _LOGGER.error("Failed to turn power off")
