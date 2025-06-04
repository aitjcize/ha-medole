"""Modbus client utilities for Medole Dehumidifier."""

# ruff: noqa: I001
import asyncio
import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from pymodbus.client import ModbusSerialClient
from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusTcpClient as ModbusRtuOverTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_PARITY,
    CONF_PORT,
    CONF_STOPBITS,
    CONF_TCP_PORT,
    CONNECTION_TYPE_RTUOVERTCP,
    CONNECTION_TYPE_SERIAL,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    DEFAULT_TCP_PORT,
)

_LOGGER = logging.getLogger(__name__)


class MedoleModbusClient:
    """Class to manage Modbus communication with Medole devices.

    This class is implemented as a singleton to ensure only one instance exists.
    Connection is kept open between operations and only reconnected when necessary.
    """

    _instances = {}

    def __new__(
        cls, hass: HomeAssistant, config: Dict[str, Any], slave_id: int
    ):
        """Create a singleton instance based on the config and slave_id."""
        connection_type = config.get(
            CONF_CONNECTION_TYPE, CONNECTION_TYPE_SERIAL
        )

        if connection_type == CONNECTION_TYPE_SERIAL:
            key = f"serial_{config.get(CONF_PORT)}_{slave_id}"
        elif connection_type == CONNECTION_TYPE_RTUOVERTCP:
            key = (
                f"rtuovertcp_{config.get(CONF_HOST)}_"
                f"{config.get(CONF_TCP_PORT, DEFAULT_TCP_PORT)}_{slave_id}"
            )
        else:
            key = (
                f"tcp_{config.get(CONF_HOST)}_"
                f"{config.get(CONF_TCP_PORT, DEFAULT_TCP_PORT)}_{slave_id}"
            )

        if key not in cls._instances:
            cls._instances[key] = super(MedoleModbusClient, cls).__new__(cls)
            cls._instances[key]._initialized = False

        return cls._instances[key]

    def __init__(
        self, hass: HomeAssistant, config: Dict[str, Any], slave_id: int
    ):
        """Initialize the Modbus client."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.hass = hass
        self.config = config
        self.slave_id = slave_id
        self.client = self._create_modbus_client()
        self.lock = asyncio.Lock()
        self.is_connected = False
        self._initialized = True

    def _create_modbus_client(self):
        """Create a modbus client based on configuration."""
        connection_type = self.config.get(
            CONF_CONNECTION_TYPE, CONNECTION_TYPE_SERIAL
        )

        # Get serial connection parameters
        if connection_type == CONNECTION_TYPE_SERIAL:
            port = self.config[CONF_PORT]
            baudrate = self.config.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
            bytesize = self.config.get(CONF_BYTESIZE, DEFAULT_BYTESIZE)
            parity = self.config.get(CONF_PARITY, DEFAULT_PARITY)
            stopbits = self.config.get(CONF_STOPBITS, DEFAULT_STOPBITS)

            return ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=1,
            )

        # Get TCP connection parameters
        host = self.config[CONF_HOST]
        port = self.config.get(CONF_TCP_PORT, DEFAULT_TCP_PORT)

        # RTU over TCP
        if connection_type == CONNECTION_TYPE_RTUOVERTCP:
            return ModbusRtuOverTcpClient(
                host=host,
                port=port,
                timeout=1,
                framer="rtu",  # Use RTU framer for RTU over TCP
            )

        # Regular TCP
        return ModbusTcpClient(
            host=host,
            port=port,
            timeout=1,
        )

    async def _ensure_connected(self) -> bool:
        """Ensure the client is connected, reconnect if necessary."""
        if not self.is_connected:
            self.is_connected = self.client.connect()
            if self.is_connected:
                _LOGGER.debug("Successfully connected to Modbus device")
            else:
                _LOGGER.error("Failed to connect to Modbus device")
        return self.is_connected

    async def async_read_register(
        self, address: int, count: int = 1
    ) -> Optional[Any]:
        """Read a register with proper connection handling and locking."""
        try:
            async with self.lock:
                if not await self._ensure_connected():
                    return None

                # Wrap the executor job in a function that handles exceptions
                def read_register_safe():
                    try:
                        return self.client.read_holding_registers(
                            address, count=count, slave=self.slave_id
                        )
                    except Exception as ex:
                        _LOGGER.error(
                            f"Exception in executor job reading register {address}: {ex}"
                        )
                        return None

                result = await self.hass.async_add_executor_job(
                    read_register_safe
                )

                if result is None:
                    # Error occurred in the executor job
                    self.is_connected = False
                    return None

                if result.isError():
                    _LOGGER.error(f"Error reading register {address}: {result}")
                    # Connection might be stale, mark as disconnected
                    self.is_connected = False
                    return None

                return result
        except ModbusException as ex:
            _LOGGER.error(f"Modbus exception reading register {address}: {ex}")
            # Mark connection as closed on exception
            self.is_connected = False
            return None

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a register with proper connection handling and locking."""
        try:
            async with self.lock:
                if not await self._ensure_connected():
                    return False

                # Wrap the executor job in a function that handles exceptions
                def write_register_safe():
                    try:
                        return self.client.write_register(
                            address, value, slave=self.slave_id
                        )
                    except Exception as ex:
                        _LOGGER.error(
                            f"Exception in executor job writing register {address}: {ex}"
                        )
                        return None

                result = await self.hass.async_add_executor_job(
                    write_register_safe
                )

                if result is None:
                    # Error occurred in the executor job
                    self.is_connected = False
                    return False

                if result.isError():
                    _LOGGER.error(f"Error writing register {address}: {result}")
                    # Connection might be stale, mark as disconnected
                    self.is_connected = False
                    return False

                return True
        except ModbusException as ex:
            _LOGGER.error(f"Modbus exception writing register {address}: {ex}")
            # Mark connection as closed on exception
            self.is_connected = False
            return False
