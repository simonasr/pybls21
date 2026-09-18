# Extended telemetry

`poll()` returns a `ClimateDevice` with the original climate fields plus these
telemetry fields. Most values come from the expanded input-register request;
`heat_exchanger_type`, `heat_exchanger_mode`,
`configured_main_heater_type`, and `configured_freeze_protection_mode` come
from the expanded holding-register request.

Register names and units follow the
[official Blauberg S21 Modbus table](https://blaubergventilatoren.de/uploads/download/b55_8_1en_a4_02_preview.pdf).

| Fields | Unit |
| --- | --- |
| `selected_temperature`, `current_temperature`, `current_intake_temperature`, `extract_air_inlet_temperature`, `exhaust_air_outlet_temperature`, `external_temperature`, `after_preheater_temperature`, `before_main_heater_temperature`, `return_water_temperature` | °C |
| `current_humidity`, `external_humidity` | % |
| `current_co2`, `external_co2` | ppm |
| `current_pm25`, `external_pm25` | µg/m³ |
| `current_voc`, `external_voc`, `analog_sensor_percent` | % |
| `rtc_battery_voltage_mv` | mV |
| `supply_airflow`, `extract_airflow` | m³/h |
| `supply_pressure`, `extract_pressure` | Pa |
| `supply_fan_speed`, `extract_fan_speed` | rpm |
| `timer_remaining_seconds` | seconds |
| `filter_remaining_minutes`, `total_working_time_minutes` | minutes |
| `filter_state`, `alarm_state`, `weekly_schedule_fan_mode`, `weekly_schedule_target_temperature` | protocol value |
| `heat_exchanger_type`, `heat_exchanger_mode` | protocol enum |
| `heat_exchanger_control_percent` | raw PID controller % |
| `heat_exchanger_status_percent` | raw bypass/rotor status % |
| `configured_main_heater_type`, `configured_freeze_protection_mode` | protocol enum |
| `preheater_pid_control_signal_percent`, `main_heater_pid_control_signal_percent` | raw protocol % |

`heat_exchanger_mode` is both reported by `poll()` and writable through
`set_heat_exchanger_mode()`. Its recovery-oriented names have hardware-specific
aliases matching the protocol actions:

| Value | Canonical mode | Bypass alias | Rotary alias |
| --- | --- | --- | --- |
| `0` | `RECOVERY_ON` | `BYPASS_CLOSED` | `ROTOR_ON` |
| `1` | `RECOVERY_OFF` | `BYPASS_OPEN` | `ROTOR_OFF` |
| `2` | `AUTO` | `AUTO` | `AUTO` |

Unavailable temperature sensors and optional humidity, CO₂, PM2.5, and VOC
sensors are returned as `None`. Zero remains a valid value for airflow,
pressure, the 0–10 V sensor, battery voltage, and timers.

The heater configuration fields report controller configuration, not detected
hardware. The preheater and main-heater PID signals are the raw controller
values from input registers 43 and 44. The documented range is 0 through 100%.
These fields do not prove that a heater is installed or active. Heater mode,
manual output, PID tuning, installer, and safety settings are intentionally not
writable through this library.

`heat_exchanger_control_percent` is the PID controller signal from input
register 45. It is not the current actuator state. The controller-reported
state comes from input register 51 as `heat_exchanger_status_percent`. Per the
protocol, a status of 0 means a fully closed bypass or a rotor at maximum
speed, while 100 means a fully open bypass or a fully stopped rotor. Consumers
that need an intuitive heat-recovery activity percentage can calculate
`100 - heat_exchanger_status_percent`.

The appended `ClimateDevice` fields have defaults, so existing keyword and
positional construction with fewer arguments remains valid. Because
`ClimateDevice` is a `NamedTuple`, versions that append telemetry change its
tuple length. Code that unpacks every value or checks the exact length must
migrate to named-attribute access before upgrading.
