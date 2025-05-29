"""Config flow for Medole Dehumidifier integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_PARITY,
    CONF_PORT,
    CONF_SLAVE_ID,
    CONF_STOPBITS,
    CONF_TCP_PORT,
    CONNECTION_TYPE_RTUOVERTCP,
    CONNECTION_TYPE_SERIAL,
    CONNECTION_TYPE_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_SLAVE_ID,
    DEFAULT_STOPBITS,
    DEFAULT_TCP_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MedoleDehumidifierConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Medole Dehumidifier."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Store the connection type and name for later steps
            self._connection_type = user_input[CONF_CONNECTION_TYPE]
            self._name = user_input[CONF_NAME]

            # Proceed to the appropriate connection configuration step
            if self._connection_type == CONNECTION_TYPE_SERIAL:
                return await self.async_step_serial()

            # Both TCP and RTU over TCP use the same configuration step
            return await self.async_step_tcp()

        # Show connection type selection form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(
                        CONF_CONNECTION_TYPE, default=CONNECTION_TYPE_SERIAL
                    ): vol.In(
                        [
                            CONNECTION_TYPE_SERIAL,
                            CONNECTION_TYPE_TCP,
                            CONNECTION_TYPE_RTUOVERTCP,
                        ]
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_serial(self, user_input=None):
        """Handle the serial connection step."""
        errors = {}

        if user_input is not None:
            try:
                # Convert slave_id from string to int and validate range
                if CONF_SLAVE_ID in user_input:
                    try:
                        slave_id = int(user_input[CONF_SLAVE_ID])
                        # Validate that slave ID is within the valid range (1-32)
                        if slave_id < 1 or slave_id > 32:
                            errors[CONF_SLAVE_ID] = "invalid_slave_id_range"
                        else:
                            user_input[CONF_SLAVE_ID] = slave_id
                    except ValueError:
                        errors[CONF_SLAVE_ID] = "invalid_slave_id"

                # If there are errors, show the form again
                if errors:
                    return self.async_show_form(
                        step_id="serial",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_PORT): str,
                                vol.Required(
                                    CONF_SLAVE_ID,
                                    default=str(DEFAULT_SLAVE_ID),
                                ): str,
                                vol.Optional(
                                    CONF_BAUDRATE, default=DEFAULT_BAUDRATE
                                ): vol.All(
                                    vol.Coerce(int),
                                    vol.In([9600, 19200, 38400, 57600, 115200]),
                                ),
                                vol.Optional(
                                    CONF_BYTESIZE, default=DEFAULT_BYTESIZE
                                ): vol.All(
                                    vol.Coerce(int), vol.In([5, 6, 7, 8])
                                ),
                                vol.Optional(
                                    CONF_PARITY, default=DEFAULT_PARITY
                                ): vol.In(["N", "E", "O"]),
                                vol.Optional(
                                    CONF_STOPBITS, default=DEFAULT_STOPBITS
                                ): vol.All(vol.Coerce(int), vol.In([1, 2])),
                            }
                        ),
                        errors=errors,
                    )

                # Combine with the connection type and name
                data = {
                    CONF_NAME: self._name,
                    CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
                    **user_input,
                }

                # Create unique ID from the name
                await self.async_set_unique_id(self._name)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._name,
                    data=data,
                )
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"

        # Show the serial configuration form
        return self.async_show_form(
            step_id="serial",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORT): str,
                    vol.Required(
                        CONF_SLAVE_ID, default=str(DEFAULT_SLAVE_ID)
                    ): str,
                    vol.Optional(
                        CONF_BAUDRATE, default=DEFAULT_BAUDRATE
                    ): vol.All(
                        vol.Coerce(int),
                        vol.In([9600, 19200, 38400, 57600, 115200]),
                    ),
                    vol.Optional(
                        CONF_BYTESIZE, default=DEFAULT_BYTESIZE
                    ): vol.All(vol.Coerce(int), vol.In([5, 6, 7, 8])),
                    vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): vol.In(
                        ["N", "E", "O"]
                    ),
                    vol.Optional(
                        CONF_STOPBITS, default=DEFAULT_STOPBITS
                    ): vol.All(vol.Coerce(int), vol.In([1, 2])),
                }
            ),
            errors=errors,
        )

    async def async_step_tcp(self, user_input=None):
        """Handle the TCP connection step."""
        errors = {}

        if user_input is not None:
            try:
                # Convert slave_id from string to int and validate range
                if CONF_SLAVE_ID in user_input:
                    try:
                        slave_id = int(user_input[CONF_SLAVE_ID])
                        # Validate that slave ID is within the valid range (1-32)
                        if slave_id < 1 or slave_id > 32:
                            errors[CONF_SLAVE_ID] = "invalid_slave_id_range"
                        else:
                            user_input[CONF_SLAVE_ID] = slave_id
                    except ValueError:
                        errors[CONF_SLAVE_ID] = "invalid_slave_id"

                # If there are errors, show the form again
                if errors:
                    return self.async_show_form(
                        step_id="tcp",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_HOST): str,
                                vol.Required(
                                    CONF_TCP_PORT, default=DEFAULT_TCP_PORT
                                ): vol.All(
                                    vol.Coerce(int),
                                    vol.Range(min=1, max=65535),
                                ),
                                vol.Required(
                                    CONF_SLAVE_ID,
                                    default=str(DEFAULT_SLAVE_ID),
                                ): str,
                            }
                        ),
                        errors=errors,
                    )

                # Combine with the connection type and name
                data = {
                    CONF_NAME: self._name,
                    CONF_CONNECTION_TYPE: self._connection_type,
                    **user_input,
                }

                # Create unique ID from the name
                await self.async_set_unique_id(self._name)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._name,
                    data=data,
                )
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"

        # Show the TCP configuration form
        return self.async_show_form(
            step_id="tcp",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(
                        CONF_TCP_PORT, default=DEFAULT_TCP_PORT
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                    vol.Required(
                        CONF_SLAVE_ID, default=str(DEFAULT_SLAVE_ID)
                    ): str,
                }
            ),
            errors=errors,
        )
