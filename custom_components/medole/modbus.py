"""Modbus client utilities for Medole Dehumidifier."""

# ruff: noqa: I001
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from pymodbus.client import (
    ModbusSerialClient,
    ModbusTcpClient,
)
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
        self._last_request_time = 0
        self._min_delay = 0.05  # 50ms minimum delay between requests
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
                timeout=3,
            )

        # Get TCP connection parameters
        host = self.config[CONF_HOST]
        port = self.config.get(CONF_TCP_PORT, DEFAULT_TCP_PORT)

        # RTU over TCP
        if connection_type == CONNECTION_TYPE_RTUOVERTCP:
            return ModbusTcpClient(
                host=host,
                port=port,
                timeout=3,
                framer="rtu",
            )

        # Regular TCP
        return ModbusTcpClient(
            host=host,
            port=port,
            timeout=3,
        )

    def _throttle_request(self):
        """Ensure minimum delay between requests to avoid overwhelming the device."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()

    def _ensure_connection(self) -> bool:
        """Ensure the client is connected."""
        # Check if already connected using pymodbus's own connection tracking
        is_connected = False
        try:
            if hasattr(self.client, "connected"):
                is_connected = self.client.connected
            elif hasattr(self.client, "is_socket_open"):
                is_connected = self.client.is_socket_open()
        except Exception as ex:
            _LOGGER.debug(
                f"Cannot verify connection status: {ex}, will attempt connect"
            )

        if is_connected:
            return True

        # Not connected, attempt to connect
        _LOGGER.debug("Modbus not connected, attempting to connect...")
        if self.client.connect():
            _LOGGER.debug("Modbus connection established")
            return True
        else:
            _LOGGER.error("Failed to establish Modbus connection")
            return False

    async def async_read_register(
        self, address: int, count: int = 1
    ) -> Optional[Any]:
        """Read a register with proper connection handling and locking."""
        try:
            async with self.lock:
                if not self._ensure_connection():
                    return None

                # Throttle requests to avoid overwhelming the device
                await self.hass.async_add_executor_job(self._throttle_request)

                result = await self.hass.async_add_executor_job(
                    lambda: self.client.read_holding_registers(
                        address, count=count, device_id=self.slave_id
                    )
                )

                if result.isError():
                    _LOGGER.error(f"Error reading register {address}: {result}")
                    return None

                return result
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionError,
            OSError,
        ) as ex:
            _LOGGER.warning(
                f"Connection broken while reading register {address}: {ex}, will reconnect on next attempt"
            )
            # Explicitly close to ensure pymodbus knows connection is dead
            try:
                self.client.close()
            except Exception:
                pass
            return None
        except ModbusException as ex:
            _LOGGER.error(f"Modbus exception reading register {address}: {ex}")
            # Close on modbus errors that indicate connection issues
            if "No response" in str(ex) or "CLOSING CONNECTION" in str(ex):
                try:
                    self.client.close()
                except Exception:
                    pass
            return None

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a register with proper connection handling and locking."""
        try:
            async with self.lock:
                if not self._ensure_connection():
                    return False

                # Throttle requests to avoid overwhelming the device
                await self.hass.async_add_executor_job(self._throttle_request)

                result = await self.hass.async_add_executor_job(
                    lambda: self.client.write_register(
                        address, value, device_id=self.slave_id
                    )
                )

                if result.isError():
                    _LOGGER.error(f"Error writing register {address}: {result}")
                    return False

                return True
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionError,
            OSError,
        ) as ex:
            _LOGGER.warning(
                f"Connection broken while writing register {address}: {ex}, will reconnect on next attempt"
            )
            # Explicitly close to ensure pymodbus knows connection is dead
            try:
                self.client.close()
            except Exception:
                pass
            return False
        except ModbusException as ex:
            _LOGGER.error(f"Modbus exception writing register {address}: {ex}")
            # Close on modbus errors that indicate connection issues
            if "No response" in str(ex) or "CLOSING CONNECTION" in str(ex):
                try:
                    self.client.close()
                except Exception:
                    pass
            return False

    async def async_write_registers(
        self, address: int, values: List[int]
    ) -> bool:
        """Write multiple registers with proper connection handling and locking."""
        try:
            async with self.lock:
                if not self._ensure_connection():
                    return False

                # Throttle requests to avoid overwhelming the device
                await self.hass.async_add_executor_job(self._throttle_request)

                result = await self.hass.async_add_executor_job(
                    lambda: self.client.write_registers(
                        address, values, device_id=self.slave_id
                    )
                )

                if result.isError():
                    _LOGGER.error(
                        f"Error writing to registers at {address}: {result}"
                    )
                    return False

                return True
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionError,
            OSError,
        ) as ex:
            _LOGGER.warning(
                f"Connection broken while writing registers at {address}: {ex}, will reconnect on next attempt"
            )
            # Explicitly close to ensure pymodbus knows connection is dead
            try:
                self.client.close()
            except Exception:
                pass
            return False
        except ModbusException as ex:
            _LOGGER.error(
                f"Modbus exception writing to registers at {address}: {ex}"
            )
            # Close on modbus errors that indicate connection issues
            if "No response" in str(ex) or "CLOSING CONNECTION" in str(ex):
                try:
                    self.client.close()
                except Exception:
                    pass
            return False

    def close(self):
        """Close the Modbus connection."""
        if self.client:
            self.client.close()
            _LOGGER.debug("Modbus connection closed")
