#!/usr/bin/env python3
"""
Test script for the Medole Dehumidifier Mock Modbus Server.
This script connects to the mock server and tests various functions.
"""
import logging
import time

# Import register definitions from common module
from medole_registers import (
    FAN_SPEED_HIGH,
    # Fan speed values
    FAN_SPEED_LOW,
    FAN_SPEED_MEDIUM,
    REG_CURRENT_SECONDS,
    REG_CURRENT_TIME,
    REG_CURRENT_WEEKDAY,
    REG_DEHUMIDIFY_MODE,
    REG_FAN_ALARM_HOURS,
    REG_FAN_OPERATION_HOURS,
    REG_FAN_SPEED,
    REG_HUMIDITY_1,
    REG_HUMIDITY_2,
    REG_HUMIDITY_SETPOINT,
    REG_OPERATION_STATUS,
    REG_PIPE_TEMPERATURE,
    REG_POWER,
    REG_PURIFY_MODE,
    # Register addresses
    REG_TEMPERATURE_1,
    REG_TEMPERATURE_2,
    REG_TIMER_FUNCTION,
    decode_operation_status,
    # Helper functions
    decode_temperature,
    decode_time,
)
from pymodbus.client import ModbusTcpClient

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
_LOGGER = logging.getLogger(__name__)


# Note: decode_operation_status and decode_time are imported from medole_registers


def test_mock_server(host="localhost", port=5020, slave_id=1):
    """Test the mock Modbus server."""
    client = ModbusTcpClient(host=host, port=port)

    try:
        # Connect to the server
        if not client.connect():
            _LOGGER.error("Failed to connect to the server")
            return False

        _LOGGER.info("Connected to the server")

        # Read sensor data
        _LOGGER.info("Reading sensor data...")

        # Temperature 1
        result = client.read_holding_registers(REG_TEMPERATURE_1, count=1, device_id=slave_id)
        if not result.isError():
            temp = decode_temperature(result.registers[0])
            _LOGGER.info(f"Temperature 1: {temp:.1f}°C")

        # Humidity 1
        result = client.read_holding_registers(REG_HUMIDITY_1, count=1, device_id=slave_id)
        if not result.isError():
            humidity = result.registers[0]
            _LOGGER.info(f"Humidity 1: {humidity}%")

        # Temperature 2
        result = client.read_holding_registers(REG_TEMPERATURE_2, count=1, device_id=slave_id)
        if not result.isError():
            temp = decode_temperature(result.registers[0])
            _LOGGER.info(f"Temperature 2: {temp:.1f}°C")

        # Humidity 2
        result = client.read_holding_registers(REG_HUMIDITY_2, count=1, device_id=slave_id)
        if not result.isError():
            humidity = result.registers[0]
            _LOGGER.info(f"Humidity 2: {humidity}%")

        # Operation status
        result = client.read_holding_registers(REG_OPERATION_STATUS, count=1, device_id=slave_id)
        if not result.isError():
            status = decode_operation_status(result.registers[0])
            _LOGGER.info(f"Operation status: {status}")

        # Pipe temperature
        result = client.read_holding_registers(REG_PIPE_TEMPERATURE, count=1, device_id=slave_id)
        if not result.isError():
            temp = decode_temperature(result.registers[0])
            _LOGGER.info(f"Pipe temperature: {temp:.1f}°C")

        # Fan operation hours
        result = client.read_holding_registers(REG_FAN_OPERATION_HOURS, count=1, device_id=slave_id)
        if not result.isError():
            hours = result.registers[0]
            _LOGGER.info(f"Fan operation hours: {hours}")

        # Fan alarm hours
        result = client.read_holding_registers(REG_FAN_ALARM_HOURS, count=1, device_id=slave_id)
        if not result.isError():
            hours = result.registers[0]
            _LOGGER.info(f"Fan alarm hours: {hours}")

        # Read control registers
        _LOGGER.info("\nReading control registers...")

        # Power
        result = client.read_holding_registers(REG_POWER, count=1, device_id=slave_id)
        if not result.isError():
            power = "On" if result.registers[0] == 1 else "Off"
            _LOGGER.info(f"Power: {power}")

        # Fan speed
        result = client.read_holding_registers(REG_FAN_SPEED, count=1, device_id=slave_id)
        if not result.isError():
            speed = result.registers[0]
            speed_text = "Low" if speed == FAN_SPEED_LOW else "Medium" if speed == FAN_SPEED_MEDIUM else "High" if speed == FAN_SPEED_HIGH else "Unknown"
            _LOGGER.info(f"Fan speed: {speed_text} ({speed})")

        # Humidity setpoint
        result = client.read_holding_registers(REG_HUMIDITY_SETPOINT, count=1, device_id=slave_id)
        if not result.isError():
            setpoint = result.registers[0]
            setpoint_text = "Continuous" if setpoint == 0 else f"{setpoint}%"
            _LOGGER.info(f"Humidity setpoint: {setpoint_text}")

        # Dehumidify mode
        result = client.read_holding_registers(REG_DEHUMIDIFY_MODE, count=1, device_id=slave_id)
        if not result.isError():
            mode = "On" if result.registers[0] == 1 else "Off"
            _LOGGER.info(f"Dehumidify mode: {mode}")

        # Purify mode
        result = client.read_holding_registers(REG_PURIFY_MODE, count=1, device_id=slave_id)
        if not result.isError():
            mode = "On" if result.registers[0] == 1 else "Off"
            _LOGGER.info(f"Purify mode: {mode}")

        # Read time function registers
        _LOGGER.info("\nReading time function registers...")

        # Current time
        result = client.read_holding_registers(REG_CURRENT_TIME, count=1, device_id=slave_id)
        if not result.isError():
            time_str = decode_time(result.registers[0])
            _LOGGER.info(f"Current time: {time_str}")

        # Current seconds
        result = client.read_holding_registers(REG_CURRENT_SECONDS, count=1, device_id=slave_id)
        if not result.isError():
            seconds = result.registers[0]
            _LOGGER.info(f"Current seconds: {seconds}")

        # Current weekday
        result = client.read_holding_registers(REG_CURRENT_WEEKDAY, count=1, device_id=slave_id)
        if not result.isError():
            weekday = result.registers[0]
            weekday_text = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][weekday - 1]
            _LOGGER.info(f"Current weekday: {weekday_text} ({weekday})")

        # Timer function
        result = client.read_holding_registers(REG_TIMER_FUNCTION, count=1, device_id=slave_id)
        if not result.isError():
            timer = result.registers[0]
            _LOGGER.info(f"Timer function: {timer}")

        # Test writing to registers
        _LOGGER.info("\nTesting write operations...")

        # Turn on power
        _LOGGER.info("Turning on power...")
        result = client.write_register(address=REG_POWER, value=1, device_id=slave_id)
        if not result.isError():
            _LOGGER.info("Power turned on")

        # Set fan speed to medium
        _LOGGER.info("Setting fan speed to medium...")
        result = client.write_register(address=REG_FAN_SPEED, value=FAN_SPEED_MEDIUM, device_id=slave_id)
        if not result.isError():
            _LOGGER.info("Fan speed set to medium")

        # Set humidity setpoint to 45%
        _LOGGER.info("Setting humidity setpoint to 45%...")
        result = client.write_register(address=REG_HUMIDITY_SETPOINT, value=45, device_id=slave_id)
        if not result.isError():
            _LOGGER.info("Humidity setpoint set to 45%")

        # Turn on dehumidify mode
        _LOGGER.info("Turning on dehumidify mode...")
        result = client.write_register(address=REG_DEHUMIDIFY_MODE, value=1, device_id=slave_id)
        if not result.isError():
            _LOGGER.info("Dehumidify mode turned on")

        # Wait a bit for the server to update
        _LOGGER.info("\nWaiting for 10 seconds to see changes...")
        time.sleep(10)

        # Read operation status again to see changes
        _LOGGER.info("\nReading operation status after changes...")
        result = client.read_holding_registers(REG_OPERATION_STATUS, count=1, device_id=slave_id)
        if not result.isError():
            status = decode_operation_status(result.registers[0])
            _LOGGER.info(f"Operation status: {status}")

        # Read humidity again to see if it's changing
        _LOGGER.info("\nReading humidity after changes...")
        result = client.read_holding_registers(REG_HUMIDITY_1, count=1, device_id=slave_id)
        if not result.isError():
            humidity = result.registers[0]
            _LOGGER.info(f"Humidity 1: {humidity}%")

        # Turn everything off
        _LOGGER.info("\nTurning everything off...")
        client.write_register(address=REG_DEHUMIDIFY_MODE, value=0, device_id=slave_id)
        client.write_register(address=REG_POWER, value=0, device_id=slave_id)
        _LOGGER.info("Power and dehumidify mode turned off")

        return True

    except Exception as e:
        _LOGGER.error(f"Error: {e}")
        return False

    finally:
        # Close the connection
        client.close()
        _LOGGER.info("Connection closed")


if __name__ == "__main__":
    # Test the mock server
    test_mock_server()
