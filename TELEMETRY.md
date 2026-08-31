# Extended telemetry

`poll()` returns a `ClimateDevice` with the original climate fields plus these
read-only measurements from the same input-register request.

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

Unavailable temperature sensors and optional humidity, CO₂, PM2.5, and VOC
sensors are returned as `None`. Zero remains a valid value for airflow,
pressure, the 0–10 V sensor, battery voltage, and timers.

The new `ClimateDevice` fields have defaults, so existing keyword and
positional construction with the original fields remains valid. Because it is
a `NamedTuple`, code that unpacks it by tuple length should switch to named
attributes before adopting this version.
