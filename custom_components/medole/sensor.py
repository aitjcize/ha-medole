"""Sensor platform for Medole Dehumidifier integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_NAME,
    DOMAIN,
    REG_FAN_ALARM_HOURS,
    REG_FAN_OPERATION_HOURS,
    REG_HUMIDITY_1,
    REG_HUMIDITY_2,
    REG_OPERATION_STATUS,
    REG_PIPE_TEMPERATURE,
    REG_TEMPERATURE_1,
    REG_TEMPERATURE_2,
    STATUS_COMPRESSOR_ON,
    STATUS_FAN_ON,
    STATUS_HIGH_PRESSURE_ERROR,
    STATUS_HUMIDITY_SENSOR_ERROR,
    STATUS_LOW_PRESSURE_ERROR,
    STATUS_PIPE_TEMP_ERROR,
    STATUS_ROOM_TEMP_ERROR,
    STATUS_WATER_FULL_ERROR,
)
from .modbus import async_read_register

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Medole Dehumidifier sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    config = data["config"]
    client = data["client"]
    slave_id = data["slave_id"]

    name = config[CONF_NAME]

    entities = [
        MedoleTemperatureSensor(hass, name, client, slave_id, 1),
        MedoleHumiditySensor(hass, name, client, slave_id, 1),
        MedolePipeTemperatureSensor(hass, name, client, slave_id),
        MedoleFanOperationHoursSensor(hass, name, client, slave_id),
        MedoleFanAlarmHoursSensor(hass, name, client, slave_id),
        MedoleStatusSensor(hass, name, client, slave_id),
    ]
    async_add_entities(entities, True)


class MedoleBaseSensor(SensorEntity):
    """Base class for Medole Dehumidifier sensors."""

    _attr_has_entity_name = True

    def __init__(self, hass, name, client, slave_id, sensor_type):
        """Initialize the sensor."""
        self.hass = hass
        self._client = client
        self._slave_id = slave_id
        self._attr_unique_id = f"{name}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{name}_humidifier")},
            "name": name,
            "manufacturer": "Medole",
            "model": "IN-D17",
        }


class MedoleTemperatureSensor(MedoleBaseSensor):
    """Representation of a Medole Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, hass, name, client, slave_id, sensor_number):
        """Initialize the temperature sensor."""
        super().__init__(
            hass, name, client, slave_id, f"temperature_{sensor_number}"
        )
        self._sensor_number = sensor_number
        self._attr_name = "Temperature"
        self._register = (
            REG_TEMPERATURE_1 if sensor_number == 1 else REG_TEMPERATURE_2
        )

    async def async_update(self) -> None:
        """Update the state of the sensor."""
        result = await async_read_register(
            self.hass, self._client, self._register, self._slave_id
        )

        if result:
            # Temperature format: Hi Byte = decimal, Lo Byte = integer
            temp_value = result.registers[0]
            integer_part = temp_value & 0xFF
            decimal_part = (temp_value >> 8) & 0xFF
            self._attr_native_value = integer_part + decimal_part / 10
        else:
            self._attr_native_value = None


class MedoleHumiditySensor(MedoleBaseSensor):
    """Representation of a Medole Humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, hass, name, client, slave_id, sensor_number):
        """Initialize the humidity sensor."""
        super().__init__(
            hass, name, client, slave_id, f"humidity_{sensor_number}"
        )
        self._sensor_number = sensor_number
        self._attr_name = "Humidity"
        self._register = (
            REG_HUMIDITY_1 if sensor_number == 1 else REG_HUMIDITY_2
        )

    async def async_update(self) -> None:
        """Update the state of the sensor."""
        result = await async_read_register(
            self.hass, self._client, self._register, self._slave_id
        )

        if result:
            self._attr_native_value = result.registers[0]
        else:
            self._attr_native_value = None


class MedolePipeTemperatureSensor(MedoleBaseSensor):
    """Representation of a Medole Pipe Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, hass, name, client, slave_id):
        """Initialize the pipe temperature sensor."""
        super().__init__(hass, name, client, slave_id, "pipe_temperature")
        self._attr_name = "Pipe Temperature"

    async def async_update(self) -> None:
        """Update the state of the sensor."""
        result = await async_read_register(
            self.hass, self._client, REG_PIPE_TEMPERATURE, self._slave_id
        )

        if result:
            self._attr_native_value = result.registers[0] / 10.0
        else:
            self._attr_native_value = None


class MedoleFanOperationHoursSensor(MedoleBaseSensor):
    """Representation of a Medole Fan Operation Hours sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, hass, name, client, slave_id):
        """Initialize the fan operation hours sensor."""
        super().__init__(hass, name, client, slave_id, "fan_operation_hours")
        self._attr_name = "Fan Operation Hours"

    async def async_update(self) -> None:
        """Update the state of the sensor."""
        result = await async_read_register(
            self.hass, self._client, REG_FAN_OPERATION_HOURS, self._slave_id
        )

        if result:
            self._attr_native_value = result.registers[0]
        else:
            self._attr_native_value = None


class MedoleFanAlarmHoursSensor(MedoleBaseSensor):
    """Representation of a Medole Fan Alarm Hours sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.HOURS

    def __init__(self, hass, name, client, slave_id):
        """Initialize the fan alarm hours sensor."""
        super().__init__(hass, name, client, slave_id, "fan_alarm_hours")
        self._attr_name = "Fan Alarm Hours"

    async def async_update(self) -> None:
        """Update the state of the sensor."""
        result = await async_read_register(
            self.hass, self._client, REG_FAN_ALARM_HOURS, self._slave_id
        )

        if result:
            self._attr_native_value = result.registers[0]
        else:
            self._attr_native_value = None


class MedoleStatusSensor(MedoleBaseSensor):
    """Representation of a Medole Status sensor."""

    def __init__(self, hass, name, client, slave_id):
        """Initialize the status sensor."""
        super().__init__(hass, name, client, slave_id, "status")
        self._attr_name = "Status"
        self._status_value = None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self._status_value is None:
            return {}

        lo_byte = self._status_value & 0xFF
        hi_byte = (self._status_value >> 8) & 0xFF

        return {
            "compressor_on": bool(lo_byte & STATUS_COMPRESSOR_ON),
            "fan_on": bool(lo_byte & STATUS_FAN_ON),
            "pipe_temp_error": bool(lo_byte & STATUS_PIPE_TEMP_ERROR),
            "humidity_sensor_error": bool(
                lo_byte & STATUS_HUMIDITY_SENSOR_ERROR
            ),
            "room_temp_error": bool(lo_byte & STATUS_ROOM_TEMP_ERROR),
            "water_full_error": bool(lo_byte & STATUS_WATER_FULL_ERROR),
            "high_pressure_error": bool(
                hi_byte & (STATUS_HIGH_PRESSURE_ERROR >> 8)
            ),
            "low_pressure_error": bool(
                hi_byte & (STATUS_LOW_PRESSURE_ERROR >> 8)
            ),
        }

    async def async_update(self) -> None:
        """Update the state of the sensor."""
        result = await async_read_register(
            self.hass, self._client, REG_OPERATION_STATUS, self._slave_id
        )

        if result:
            self._status_value = result.registers[0]

            # Set the state based on errors
            errors = []
            lo_byte = self._status_value & 0xFF
            hi_byte = (self._status_value >> 8) & 0xFF

            if lo_byte & STATUS_PIPE_TEMP_ERROR:
                errors.append("pipe_temp_error")
            if lo_byte & STATUS_HUMIDITY_SENSOR_ERROR:
                errors.append("humidity_sensor_error")
            if lo_byte & STATUS_ROOM_TEMP_ERROR:
                errors.append("room_temp_error")
            if lo_byte & STATUS_WATER_FULL_ERROR:
                errors.append("water_full_error")
            if hi_byte & (STATUS_HIGH_PRESSURE_ERROR >> 8):
                errors.append("high_pressure_error")
            if hi_byte & (STATUS_LOW_PRESSURE_ERROR >> 8):
                errors.append("low_pressure_error")

            if errors:
                self._attr_native_value = "Error: " + ", ".join(errors)
            elif lo_byte & STATUS_COMPRESSOR_ON:
                self._attr_native_value = "Dehumidifying"
            elif lo_byte & STATUS_FAN_ON:
                self._attr_native_value = "Fan Only"
            else:
                self._attr_native_value = "Idle"
        else:
            self._attr_native_value = "Communication Error"
            self._status_value = None
