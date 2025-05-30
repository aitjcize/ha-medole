"""Constants for the Medole Dehumidifier integration."""

DOMAIN = "medole"

# Configuration
CONF_NAME = "name"
CONF_SLAVE_ID = "slave_id"
CONF_PORT = "port"
CONF_BAUDRATE = "baudrate"
CONF_BYTESIZE = "bytesize"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"

# Connection type
CONF_CONNECTION_TYPE = "connection_type"
CONNECTION_TYPE_SERIAL = "serial"
CONNECTION_TYPE_TCP = "tcp"
CONNECTION_TYPE_RTUOVERTCP = "rtuovertcp"

# TCP Configuration
CONF_HOST = "host"
CONF_TCP_PORT = "tcp_port"

# Default values
DEFAULT_SLAVE_ID = 1
DEFAULT_BAUDRATE = 9600
DEFAULT_BYTESIZE = 8
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_TCP_PORT = 502

# Modbus registers
REG_TEMPERATURE_1 = 0x6101
REG_HUMIDITY_1 = 0x6102
REG_TEMPERATURE_2 = 0x6103
REG_HUMIDITY_2 = 0x6104
REG_OPERATION_STATUS = 0x6105
REG_PIPE_TEMPERATURE = 0x6106
REG_FAN_OPERATION_HOURS = 0x6111
REG_FAN_ALARM_HOURS = 0x6112

REG_POWER = 0x6201
REG_FAN_SPEED = 0x6202
REG_HUMIDITY_SETPOINT = 0x6203
REG_DEHUMIDIFY_MODE = 0x6205
REG_PURIFY_MODE = 0x6206

# Operation status bits
STATUS_COMPRESSOR_ON = 0x80  # bit7
STATUS_FAN_ON = 0x40  # bit6
STATUS_PIPE_TEMP_ERROR = 0x10  # bit4
STATUS_HUMIDITY_SENSOR_ERROR = 0x08  # bit3
STATUS_ROOM_TEMP_ERROR = 0x04  # bit2
STATUS_WATER_FULL_ERROR = 0x02  # bit1
STATUS_HIGH_PRESSURE_ERROR = 0x0800  # Hi Byte bit3
STATUS_LOW_PRESSURE_ERROR = 0x0400  # Hi Byte bit2

# Fan speed values
FAN_SPEED_LOW = 1
FAN_SPEED_MEDIUM = 2
FAN_SPEED_HIGH = 3

# Continuous dehumidification
CONTINUOUS_DEHUMIDIFICATION = 0

# Min/Max humidity setpoint
MIN_HUMIDITY = 20
MAX_HUMIDITY = 90
