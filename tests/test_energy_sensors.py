# tests/test_energy_sensors.py
"""Tests for energy accumulation sensors."""

from unittest.mock import MagicMock
import pytest

from custom_components.pecron.sensor import PECRON_SENSORS, PecronSensor


ENERGY_SENSOR_KEYS = [
    "pv_generation_session",
    "pv_generation_total",
    "ac_charge_session",
    "ac_charge_total",
    "dc_output_session",
    "dc_output_total",
    "ac_output_session",
    "ac_output_total",
]

ENERGY_RAW_CODES = {
    "pv_generation_session": "solar_panel_power_generation",
    "pv_generation_total": "total_energy",
    "ac_charge_session": "ac_charge_energy",
    "ac_charge_total": "total_ac_charge_energy",
    "dc_output_session": "dc_output_energy",
    "dc_output_total": "total_dc_output_energy",
    "ac_output_session": "ac_output_energy",
    "ac_output_total": "total_ac_output_energy",
}


def make_props_with_raw(raw_values: dict):
    props = MagicMock()
    props.get_by_code = lambda code: raw_values.get(code)
    return props


def make_sensor(key, props):
    desc = next(s for s in PECRON_SENSORS if s.key == key)
    device = MagicMock()
    device.device_key = "test_key"
    device.device_name = "Test Device"
    device.product_name = "F3000LFP"
    coordinator = MagicMock()
    coordinator.data = {
        "test_key": {
            "device": device,
            "properties": props,
        }
    }
    return PecronSensor(coordinator, "test_key", device, desc)


class TestSensorDescriptionFields:
    @pytest.mark.parametrize("key", ENERGY_SENSOR_KEYS)
    def test_sensor_exists(self, key):
        desc = next((s for s in PECRON_SENSORS if s.key == key), None)
        assert desc is not None, f"Sensor with key '{key}' not found in PECRON_SENSORS"

    @pytest.mark.parametrize("key,raw_code", ENERGY_RAW_CODES.items())
    def test_raw_code_matches_tsl_property(self, key, raw_code):
        desc = next(s for s in PECRON_SENSORS if s.key == key)
        assert desc.raw_code == raw_code

    @pytest.mark.parametrize("key", ENERGY_SENSOR_KEYS)
    def test_unit_is_kwh(self, key):
        from homeassistant.const import UnitOfEnergy
        desc = next(s for s in PECRON_SENSORS if s.key == key)
        assert desc.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR

    @pytest.mark.parametrize("key", ENERGY_SENSOR_KEYS)
    def test_state_class_is_total_increasing(self, key):
        from homeassistant.components.sensor import SensorStateClass
        desc = next(s for s in PECRON_SENSORS if s.key == key)
        assert desc.state_class == SensorStateClass.TOTAL_INCREASING

    @pytest.mark.parametrize("key", ENERGY_SENSOR_KEYS)
    def test_device_class_is_energy(self, key):
        from homeassistant.components.sensor import SensorDeviceClass
        desc = next(s for s in PECRON_SENSORS if s.key == key)
        assert desc.device_class == SensorDeviceClass.ENERGY

    @pytest.mark.parametrize("key", ENERGY_SENSOR_KEYS)
    def test_not_always_create(self, key):
        desc = next(s for s in PECRON_SENSORS if s.key == key)
        assert desc.always_create is False


class TestEnergyNativeValue:
    def test_pv_generation_total_returns_float(self):
        props = make_props_with_raw({"total_energy": "8.737"})
        sensor = make_sensor("pv_generation_total", props)
        assert sensor.native_value == pytest.approx(8.737)

    def test_ac_output_total_returns_float(self):
        props = make_props_with_raw({"total_ac_output_energy": "138.863"})
        sensor = make_sensor("ac_output_total", props)
        assert sensor.native_value == pytest.approx(138.863)

    def test_zero_value_returns_zero(self):
        props = make_props_with_raw({"dc_output_energy": "0"})
        sensor = make_sensor("dc_output_session", props)
        assert sensor.native_value == pytest.approx(0.0)

    def test_returns_none_when_raw_code_missing(self):
        props = make_props_with_raw({})
        sensor = make_sensor("pv_generation_total", props)
        assert sensor.native_value is None

    def test_returns_none_for_invalid_string(self):
        props = make_props_with_raw({"total_energy": "N/A"})
        sensor = make_sensor("pv_generation_total", props)
        assert sensor.native_value is None

    def test_returns_none_when_coordinator_data_none(self):
        props = make_props_with_raw({"total_energy": "8.737"})
        sensor = make_sensor("pv_generation_total", props)
        sensor.coordinator.data = None
        assert sensor.native_value is None

    def test_returns_none_when_device_not_in_coordinator(self):
        props = make_props_with_raw({"total_energy": "8.737"})
        sensor = make_sensor("pv_generation_total", props)
        sensor.coordinator.data = {}
        assert sensor.native_value is None

    @pytest.mark.parametrize("key,raw_code,value", [
        ("pv_generation_session", "solar_panel_power_generation", "0"),
        ("pv_generation_total", "total_energy", "8.737"),
        ("ac_charge_session", "ac_charge_energy", "166.38"),
        ("ac_charge_total", "total_ac_charge_energy", "166.38"),
        ("dc_output_session", "dc_output_energy", "0"),
        ("dc_output_total", "total_dc_output_energy", "0"),
        ("ac_output_session", "ac_output_energy", "138.86"),
        ("ac_output_total", "total_ac_output_energy", "138.86"),
    ])
    def test_all_sensors_return_float(self, key, raw_code, value):
        props = make_props_with_raw({raw_code: value})
        sensor = make_sensor(key, props)
        assert isinstance(sensor.native_value, float)
        assert sensor.native_value == pytest.approx(float(value))


class TestTslFiltering:
    def _make_tsl_prop(self, code):
        p = MagicMock()
        p.code = code
        return p

    def test_energy_sensor_created_when_raw_code_in_tsl(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("total_energy")]
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl)
        keys = [s.entity_description.key for s in sensors]
        assert "pv_generation_total" in keys

    def test_energy_sensor_skipped_when_raw_code_absent(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("battery_percentage")]
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl)
        keys = [s.entity_description.key for s in sensors]
        assert "pv_generation_total" not in keys

    def test_all_energy_sensors_created_when_tsl_is_none(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl=None)
        keys = [s.entity_description.key for s in sensors]
        for key in ENERGY_SENSOR_KEYS:
            assert key in keys, f"Expected energy sensor '{key}' to be created with no TSL"
