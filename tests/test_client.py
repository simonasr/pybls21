import unittest
from unittest.mock import AsyncMock, Mock

from pyModbusTCP.server import DataBank, ModbusServer

from pybls21.client import S21Client
from pybls21.constants import *
from pybls21.exceptions import *
from pybls21.models import ClimateDevice, ClimateEntityFeature, HVACAction, HVACMode


class ErrorResponse:
    def isError(self):
        return True

    def __repr__(self):
        return "ErrorResponse()"


class SuccessResponse:
    def __init__(self, *, registers=None, bits=None):
        self.registers = registers
        self.bits = bits

    def isError(self):
        return False


class TestClient(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ModbusServer(
            host="localhost", port=5502, no_block=True, data_bank=TestDataBank()
        )
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        self.server.data_bank.reset()

    async def test_poll_when_device_type_is_incorrect_raises_exception(self):
        self.server.data_bank.set_input_registers(IR_DeviceTYPE, [0])

        client = S21Client(host=self.server.host, port=self.server.port)
        with self.assertRaises(UnsupportedDeviceException):
            await client.poll()

    async def test_poll_when_connection_fails_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=False)
        client.client.close = Mock()

        with self.assertRaises(ModbusCommunicationException):
            await client.poll()

    async def test_poll_when_modbus_returns_error_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)
        client.client.close = Mock()
        client.client.read_input_registers = AsyncMock(return_value=ErrorResponse())

        with self.assertRaises(ModbusCommunicationException):
            await client.poll()

    async def test_poll_when_modbus_returns_empty_response_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)
        client.client.close = Mock()
        client.client.read_input_registers = AsyncMock(return_value=None)

        with self.assertRaises(ModbusCommunicationException):
            await client.poll()

    async def test_poll_when_register_count_is_incomplete_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)
        client.client.close = Mock()
        client.client.read_input_registers = AsyncMock(
            return_value=SuccessResponse(registers=[1])
        )
        client.client.read_coils = AsyncMock(
            return_value=SuccessResponse(bits=[False] * 4)
        )
        client.client.read_holding_registers = AsyncMock(
            return_value=SuccessResponse(registers=[0] * 10)
        )

        with self.assertRaises(ModbusCommunicationException):
            await client.poll()

    async def test_turn_on_when_write_fails_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)
        client.client.close = Mock()
        client.client.write_coil = AsyncMock(return_value=ErrorResponse())

        with self.assertRaises(ModbusCommunicationException):
            await client.turn_on()

    async def test_poll(self):
        self.server.data_bank.set_coils(CL_POWER, [True])
        self.server.data_bank.set_coils(CL_Boost_MODE, [False])
        self.server.data_bank.set_holding_registers(HR_SetTEMP, [15])
        self.server.data_bank.set_holding_registers(HR_MaxSPEED_MODE, [3])
        self.server.data_bank.set_holding_registers(HR_SPEED_MODE, [2])
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [0])
        self.server.data_bank.set_holding_registers(HR_ManualSPEED, [100])
        self.server.data_bank.set_input_registers(
            0,
            [
                215,  # selected temperature: 21.5 °C
                108,  # supply air in: 10.8 °C
                192,  # supply air out: 19.2 °C
                201,  # extract air in: 20.1 °C
                78,  # exhaust air out: 7.8 °C
                0xFFF6,  # external temperature: -1.0 °C
                123,  # after preheater: 12.3 °C
                234,  # before main heater: 23.4 °C
                345,  # water temperature: 34.5 °C
                3000,  # RTC battery: 3000 mV
                48,  # main humidity
                55,  # external humidity
                650,  # main CO2
                700,  # external CO2
                12,  # main PM2.5
                18,  # external PM2.5
                35,  # main VOC
                40,  # external VOC
                64,  # 0-10 V sensor
                220,  # supply airflow
                210,  # extract airflow
                125,  # supply pressure
                120,  # extract pressure
                1010,  # supply fan RPM
                990,  # extract fan RPM
                0x0203,  # timer: 2 minutes, 3 seconds
                0xAB01,  # timer: 1 hour; high byte is unused
                0x0405,  # filter timer: 4 hours, 5 minutes
                2,  # filter timer: 2 days
                0x0607,  # motor time: 6 hours, 7 minutes
                300,  # motor time: 300 days
                3,  # filter state
                4,  # weekly schedule fan mode
                22,  # weekly schedule target temperature
                36,  # firmware major/minor
                2053,  # firmware day/month
                2019,  # firmware year
                1,  # device type
                2,  # alarm state
            ],
        )

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(
            device,
            ClimateDevice(
                available=True,
                name="Blauberg S21",
                unique_id=f"S21_{self.server.host}_{self.server.port}",
                temperature_unit="°C",
                precision=1,
                current_temperature=19.2,
                target_temperature=15,
                target_temperature_step=1,
                min_temp=15,
                max_temp=30,
                current_humidity=48,
                hvac_mode=HVACMode.FAN_ONLY,
                hvac_action=HVACAction.FAN,
                hvac_modes=[
                    HVACMode.OFF,
                    HVACMode.HEAT,
                    HVACMode.COOL,
                    HVACMode.AUTO,
                    HVACMode.FAN_ONLY,
                ],
                fan_mode=2,
                fan_modes=[1, 2, 3, 255],
                supported_features=ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE,
                manufacturer="Blauberg",
                model="S21",
                sw_version="0.36 (2019-05-08)",
                is_boosting=False,
                current_intake_temperature=10.8,
                manual_fan_speed_percent=100,
                max_fan_level=3,
                filter_state=3,
                alarm_state=2,
                supply_fan_speed=1010,
                extract_fan_speed=990,
                selected_temperature=21.5,
                extract_air_inlet_temperature=20.1,
                exhaust_air_outlet_temperature=7.8,
                external_temperature=-1.0,
                after_preheater_temperature=12.3,
                before_main_heater_temperature=23.4,
                return_water_temperature=34.5,
                rtc_battery_voltage_mv=3000,
                external_humidity=55,
                current_co2=650,
                external_co2=700,
                current_pm25=12,
                external_pm25=18,
                current_voc=35,
                external_voc=40,
                analog_sensor_percent=64,
                supply_airflow=220,
                extract_airflow=210,
                supply_pressure=125,
                extract_pressure=120,
                timer_remaining_seconds=3723,
                filter_remaining_minutes=3125,
                total_working_time_minutes=432367,
                weekly_schedule_fan_mode=4,
                weekly_schedule_target_temperature=22,
            ),
        )

    async def test_poll_when_optional_sensors_are_absent(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertIsNone(device.current_humidity)
        self.assertIsNone(device.external_humidity)
        self.assertIsNone(device.current_co2)
        self.assertIsNone(device.external_co2)
        self.assertIsNone(device.current_pm25)
        self.assertIsNone(device.external_pm25)
        self.assertIsNone(device.current_voc)
        self.assertIsNone(device.external_voc)
        self.assertEqual(device.analog_sensor_percent, 0)
        self.assertEqual(device.supply_airflow, 0)
        self.assertEqual(device.supply_pressure, 0)

    async def test_poll_when_temperature_sensors_are_unavailable(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(
            IR_CurSelTEMP,
            [
                0x8000,
                0x7FFF,
                0x8000,
                0x7FFF,
                0x8000,
                0x7FFF,
                0x8000,
                0x7FFF,
                0x8000,
            ],
        )

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertIsNone(device.selected_temperature)
        self.assertIsNone(device.current_intake_temperature)
        self.assertIsNone(device.current_temperature)
        self.assertIsNone(device.extract_air_inlet_temperature)
        self.assertIsNone(device.exhaust_air_outlet_temperature)
        self.assertIsNone(device.external_temperature)
        self.assertIsNone(device.after_preheater_temperature)
        self.assertIsNone(device.before_main_heater_temperature)
        self.assertIsNone(device.return_water_temperature)
        self.assertEqual(device.hvac_action, HVACAction.IDLE)

    async def test_failed_reconnect_marks_previously_polled_device_unavailable(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        await client.poll()
        client.client.connect = AsyncMock(return_value=False)

        with self.assertRaises(ModbusCommunicationException):
            await client.poll()

        self.assertFalse(client.device.available)

    async def test_poll_error_marks_previously_polled_device_unavailable(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        await client.poll()
        client.client.connect = AsyncMock(return_value=True)
        client.client.close = Mock()
        client.client.read_input_registers = AsyncMock(return_value=ErrorResponse())

        with self.assertRaises(ModbusCommunicationException):
            await client.poll()

        self.assertFalse(client.device.available)

    def test_climate_device_legacy_constructor_keeps_new_fields_optional(self):
        device = ClimateDevice(
            available=True,
            name="Blauberg S21",
            unique_id="test-device",
            temperature_unit="°C",
            precision=1,
            current_temperature=20.0,
            target_temperature=21,
            target_temperature_step=1,
            min_temp=15,
            max_temp=30,
            current_humidity=None,
            hvac_mode=HVACMode.OFF,
            hvac_action=HVACAction.OFF,
            hvac_modes=[],
            fan_mode=None,
            fan_modes=None,
            supported_features=0,
            manufacturer="Blauberg",
            model="S21",
            sw_version=None,
            is_boosting=False,
            current_intake_temperature=None,
            manual_fan_speed_percent=0,
            max_fan_level=3,
            filter_state=0,
            alarm_state=0,
            supply_fan_speed=0,
            extract_fan_speed=0,
        )

        self.assertIsNone(device.selected_temperature)
        self.assertIsNone(device.current_co2)
        self.assertIsNone(device.timer_remaining_seconds)

    async def test_poll_when_device_is_off(self):
        self.server.data_bank.set_coils(CL_POWER, [False])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.OFF)
        self.assertEqual(device.hvac_action, HVACAction.OFF)

    async def test_poll_when_humidity_is_available(self):
        self.server.data_bank.set_input_registers(IR_CurRH_Int, [42])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.current_humidity, 42)

    async def test_poll_when_ventilation_only_mode_is_set(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [0])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.FAN_ONLY)
        self.assertEqual(device.hvac_action, HVACAction.FAN)

    async def test_poll_when_heating_mode_is_set(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [1])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [5])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.HEAT)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_poll_when_cooling_mode_is_set(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [2])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.COOL)
        self.assertEqual(device.hvac_action, HVACAction.COOLING)

    async def test_poll_when_temperature_registers_are_negative_values(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [0xFFF6])  # -1.0 C
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [100])  # 10.0 C

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.current_intake_temperature, -1.0)
        self.assertEqual(device.current_temperature, 10.0)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_poll_when_auto_mode_is_set_and_output_temperature_is_bigger(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_poll_when_auto_mode_is_set_and_temperature_is_reached(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [20])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.IDLE)

    async def test_poll_when_auto_mode_is_set_and_output_temperature_is_lower(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [5])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.COOLING)

    async def test_poll_when_auto_mode_is_set_and_in_temperature_matches_out_temperature(
        self,
    ):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [10])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.IDLE)

    async def test_poll_when_auto_mode_is_set_and_in_temperature_is_cooler_than_out_temperature(
        self,
    ):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [5])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [10])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_poll_when_auto_mode_is_set_and_in_temperature_is_hotter_than_out_temperature(
        self,
    ):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [5])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.COOLING)

    async def test_poll_when_is_boosting(self):
        self.server.data_bank.set_coils(CL_Boost_MODE, [True])

        client = S21Client(host=self.server.host, port=self.server.port)
        device = await client.poll()

        self.assertTrue(device.is_boosting)

    async def test_turn_on(self):
        self.server.data_bank.set_coils(CL_POWER, [False])
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [10])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.turn_on()
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.IDLE)

    async def test_turn_off(self):
        self.server.data_bank.set_coils(CL_POWER, [True])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.turn_off()
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.OFF)
        self.assertEqual(device.hvac_action, HVACAction.OFF)

    async def test_set_hvac_mode_off(self):
        self.server.data_bank.set_coils(CL_POWER, [True])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_hvac_mode(HVACMode.OFF)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.OFF)
        self.assertEqual(device.hvac_action, HVACAction.OFF)

    async def test_set_hvac_mode_heat(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_hvac_mode(HVACMode.HEAT)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.HEAT)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_set_hvac_mode_cool(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [5])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_hvac_mode(HVACMode.COOL)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.COOL)
        self.assertEqual(device.hvac_action, HVACAction.COOLING)

    async def test_set_hvac_mode_auto(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [1])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_hvac_mode(HVACMode.AUTO)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_set_hvac_mode_fan_only(self):
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [3])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_hvac_mode(HVACMode.FAN_ONLY)
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.FAN_ONLY)
        self.assertEqual(device.hvac_action, HVACAction.FAN)

    async def test_set_hvac_mode_unknown_defaults_to_auto(self):
        self.server.data_bank.set_coils(CL_POWER, [False])
        self.server.data_bank.set_holding_registers(HR_OPERATION_MODE, [0])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirIn, [10])
        self.server.data_bank.set_input_registers(IR_CurTEMP_SuAirOut, [20])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_hvac_mode("unexpected-mode")
        device = await client.poll()

        self.assertEqual(device.hvac_mode, HVACMode.AUTO)
        self.assertEqual(device.hvac_action, HVACAction.HEATING)

    async def test_set_fan_mode_level2(self):
        self.server.data_bank.set_holding_registers(HR_SPEED_MODE, [1])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_fan_mode(2)
        device = await client.poll()

        self.assertEqual(device.fan_mode, 2)

    async def test_set_fan_mode_custom(self):
        self.server.data_bank.set_holding_registers(HR_SPEED_MODE, [1])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_fan_mode(255)
        device = await client.poll()

        self.assertEqual(device.fan_mode, 255)

    async def test_set_fan_mode_when_value_is_invalid_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)

        for invalid_mode in (0, 6, 254):
            with self.subTest(mode=invalid_mode):
                with self.assertRaises(ValueError):
                    await client.set_fan_mode(invalid_mode)

        client.client.connect.assert_not_called()

    async def test_set_manual_fan_speed_percent(self):
        self.server.data_bank.set_holding_registers(HR_ManualSPEED, [0])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_manual_fan_speed_percent(42)
        device = await client.poll()

        self.assertEqual(device.manual_fan_speed_percent, 42)

    async def test_set_manual_fan_speed_percent_when_value_is_invalid_raises_exception(
        self,
    ):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)

        for invalid_speed in (-1, 101):
            with self.subTest(speed=invalid_speed):
                with self.assertRaises(ValueError):
                    await client.set_manual_fan_speed_percent(invalid_speed)

        client.client.connect.assert_not_called()

    async def test_set_temperature(self):
        self.server.data_bank.set_holding_registers(HR_SetTEMP, [0])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.set_temperature(20)
        device = await client.poll()

        self.assertEqual(device.target_temperature, 20)

    async def test_set_temperature_when_value_is_invalid_raises_exception(self):
        client = S21Client(host=self.server.host, port=self.server.port)
        client.client.connect = AsyncMock(return_value=True)

        for invalid_temperature in (14, 31):
            with self.subTest(temperature=invalid_temperature):
                with self.assertRaises(ValueError):
                    await client.set_temperature(invalid_temperature)

        client.client.connect.assert_not_called()

    async def test_reset_alarm(self):
        self.server.data_bank.set_coils(CL_RESET_ALARM, [False])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.reset_alarm()

        self.assertEqual(self.server.data_bank.get_coils(CL_RESET_ALARM, 1), [True])

    async def test_boost_on(self):
        self.server.data_bank.set_coils(CL_BoostSWITCH_CTRL, [False])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.boost_on()

        self.assertEqual(self.server.data_bank.get_coils(CL_BoostSWITCH_CTRL, 1), [True])

    async def test_boost_off(self):
        self.server.data_bank.set_coils(CL_BoostSWITCH_CTRL, [True])

        client = S21Client(host=self.server.host, port=self.server.port)
        await client.boost_off()

        self.assertEqual(self.server.data_bank.get_coils(CL_BoostSWITCH_CTRL, 1), [False])


class TestDataBank(DataBank):
    __test__ = False

    def __init__(self):
        super().__init__(
            coils_size=25, d_inputs_size=72, h_regs_size=182, i_regs_size=51
        )
        self.reset()

    def reset(self):
        # Clear server state
        self.set_coils(0, [False] * self.coils_size)
        self.set_discrete_inputs(0, [0] * self.d_inputs_size)
        self.set_holding_registers(0, [0] * self.h_regs_size)
        self.set_input_registers(0, [0] * self.i_regs_size)

        # Set some default values
        self.set_input_registers(IR_DeviceTYPE, [1])
        self.set_coils(CL_POWER, [True])
