from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class HealthErrorCode(Enum):
    TEMPERATURE_SENSOR_INVALID = 1001
    TIMESTAMP_MISSING = 1002
    ZIGBEE_DEVICES_UNHEALTHY = 1003
    SENSOR_DATA_NOT_UPDATED = 1004
    TEMPERATURE_SENSOR_FROZEN = 1005
    SYSTEM_OVERHEATED = 1006

class HealthWarningCode(Enum):
    TEMPERATURE_CONTROL_LOW = 2001
    TEMPERATURE_CONTROL_HIGH = 2002
    CO2_CONTROL_LOW = 2003
    CO2_CONTROL_HIGH = 2004
    HUMIDITY_CONTROL_LOW = 2005
    HUMIDITY_CONTROL_HIGH = 2006

@dataclass
class HealthError:
    code: HealthErrorCode
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_timestamp: datetime = None

@dataclass
class HealthWarning:
    code: HealthWarningCode
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_timestamp: datetime = None