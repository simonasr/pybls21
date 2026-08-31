from enum import Enum
from typing import List, NamedTuple, Optional

TEMP_CELSIUS: str = "°C"


class ClimateEntityFeature(int, Enum):
    TARGET_TEMPERATURE = 1
    FAN_MODE = 8


class HVACMode(str, Enum):
    OFF = "off"
    HEAT = "heat"
    COOL = "cool"
    AUTO = "auto"
    FAN_ONLY = "fan_only"


class HVACAction(str, Enum):
    COOLING = "cooling"
    FAN = "fan"
    HEATING = "heating"
    IDLE = "idle"
    OFF = "off"


class ClimateDevice(NamedTuple):
    available: bool
    name: str
    unique_id: str
    temperature_unit: str
    precision: float
    current_temperature: Optional[float]
    target_temperature: float
    target_temperature_step: float
    max_temp: float
    min_temp: float
    current_humidity: Optional[float]
    hvac_mode: str
    hvac_action: str
    hvac_modes: List[str]
    fan_mode: Optional[int]
    fan_modes: Optional[List[int]]
    supported_features: int
    manufacturer: str
    model: Optional[str]
    sw_version: Optional[str]
    is_boosting: bool
    current_intake_temperature: Optional[float]
    manual_fan_speed_percent: int
    max_fan_level: int
    filter_state: int
    alarm_state: int
    supply_fan_speed: int
    extract_fan_speed: int
    selected_temperature: Optional[float] = None
    extract_air_inlet_temperature: Optional[float] = None
    exhaust_air_outlet_temperature: Optional[float] = None
    external_temperature: Optional[float] = None
    after_preheater_temperature: Optional[float] = None
    before_main_heater_temperature: Optional[float] = None
    return_water_temperature: Optional[float] = None
    rtc_battery_voltage_mv: Optional[int] = None
    external_humidity: Optional[float] = None
    current_co2: Optional[int] = None
    external_co2: Optional[int] = None
    current_pm25: Optional[int] = None
    external_pm25: Optional[int] = None
    current_voc: Optional[int] = None
    external_voc: Optional[int] = None
    analog_sensor_percent: Optional[int] = None
    supply_airflow: Optional[int] = None
    extract_airflow: Optional[int] = None
    supply_pressure: Optional[int] = None
    extract_pressure: Optional[int] = None
    timer_remaining_seconds: Optional[int] = None
    filter_remaining_minutes: Optional[int] = None
    total_working_time_minutes: Optional[int] = None
    weekly_schedule_fan_mode: Optional[int] = None
    weekly_schedule_target_temperature: Optional[int] = None
