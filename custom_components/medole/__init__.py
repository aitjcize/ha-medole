"""The Medole Dehumidifier integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SLAVE_ID, DOMAIN
from .modbus import MedoleModbusClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.HUMIDIFIER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Medole Dehumidifier from a config entry."""
    config = entry.data

    # Create the Modbus client once
    slave_id = config[CONF_SLAVE_ID]
    modbus_client = MedoleModbusClient(hass, config, slave_id)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": modbus_client,
        "config": config,
        "slave_id": slave_id,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        # Close the Modbus connection
        data = hass.data[DOMAIN].pop(entry.entry_id)
        if "client" in data:
            data["client"].close()

    return unload_ok
