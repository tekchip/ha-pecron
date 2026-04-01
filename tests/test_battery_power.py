# tests/test_battery_power.py
"""Tests for Battery Power sensor (struct_product + negate_value)."""

import pytest
from unittest.mock import MagicMock

from custom_components.pecron.sensor import PECRON_SENSORS, PecronSensor


def make_sensor(key, battery_pack_dict):
    desc = next(s for s in PECRON_SENSORS if s.key == key)
    device = MagicMock()
    device.device_key = "test_key"
    device.device_name = "Test Device"
    device.product_name = "F3000LFP"
    props = MagicMock()
    props.battery_pack = battery_pack_dict
    coordinator = MagicMock()
    coordinator.data = {
        "test_key": {"device": device, "properties": props}
    }
    return PecronSensor(coordinator, "test_key", device, desc)


class TestBatteryPowerDescription:
    def test_sensor_exists(self):
        desc = next((s for s in PECRON_SENSORS if s.key == "battery_pack"), None)
        assert desc is not None

    def test_struct_product_fields(self):
        desc = next(s for s in PECRON_SENSORS if s.key == "battery_pack")
        assert desc.struct_product == ("host_packet_current", "host_packet_voltage")

    def test_negate_value_is_false(self):
        desc = next(s for s in PECRON_SENSORS if s.key == "battery_pack")
        assert desc.negate_value is False

    def test_unit_is_watt(self):
        from homeassistant.const import UnitOfPower
        desc = next(s for s in PECRON_SENSORS if s.key == "battery_pack")
        assert desc.native_unit_of_measurement == UnitOfPower.WATT

    def test_device_class_is_power(self):
        from homeassistant.components.sensor import SensorDeviceClass
        desc = next(s for s in PECRON_SENSORS if s.key == "battery_pack")
        assert desc.device_class == SensorDeviceClass.POWER

    def test_tsl_code(self):
        desc = next(s for s in PECRON_SENSORS if s.key == "battery_pack")
        assert desc.tsl_code == "host_packet_data_jdb"


class TestBatteryPowerNativeValue:
    def test_charging_returns_positive(self):
        # Device reports positive current when charging
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "0.82",
            "host_packet_voltage": "53.4",
        })
        assert sensor.native_value == pytest.approx(0.82 * 53.4, abs=0.1)
        assert sensor.native_value > 0

    def test_discharging_returns_negative(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "-5.0",
            "host_packet_voltage": "52.0",
        })
        assert sensor.native_value == pytest.approx(-260.0, abs=0.1)
        assert sensor.native_value < 0

    def test_idle_near_zero(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "0.0",
            "host_packet_voltage": "53.0",
        })
        assert sensor.native_value == pytest.approx(0.0, abs=0.1)

    def test_returns_none_when_current_missing(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_voltage": "53.4",
        })
        assert sensor.native_value is None

    def test_returns_none_when_voltage_missing(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "-0.32",
        })
        assert sensor.native_value is None

    def test_returns_none_when_battery_pack_none(self):
        sensor = make_sensor("battery_pack", None)
        assert sensor.native_value is None

    def test_returns_none_when_coordinator_empty(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "-0.32",
            "host_packet_voltage": "53.4",
        })
        sensor.coordinator.data = None
        assert sensor.native_value is None

    def test_returns_none_for_invalid_string(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "N/A",
            "host_packet_voltage": "53.4",
        })
        assert sensor.native_value is None

    def test_result_is_rounded_to_one_decimal(self):
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "1.123456789",
            "host_packet_voltage": "53.123456789",
        })
        result = sensor.native_value
        assert result is not None
        assert result == round(1.123456789 * 53.123456789, 1)

    def test_live_data_example(self):
        # Values observed from live F3000LFP at 93% battery, charging from solar
        # Device reports positive current when charging (+0.82A observed with remain_charging_time=154)
        sensor = make_sensor("battery_pack", {
            "host_packet_current": "0.819999992847443",
            "host_packet_voltage": "53.4029998779297",
        })
        result = sensor.native_value
        assert result is not None
        assert result > 0   # Should be positive (charging)
        assert result == pytest.approx(0.82 * 53.4, abs=1.0)


class TestTslFiltering:
    def _make_tsl_prop(self, code):
        p = MagicMock()
        p.code = code
        return p

    def test_battery_power_created_when_tsl_code_in_tsl(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("host_packet_data_jdb")]
        device = MagicMock(device_name="Test")
        sensors = create_sensors_for_device_helper(MagicMock(), "key", device, tsl)
        assert any(s.entity_description.key == "battery_pack" for s in sensors)

    def test_battery_power_skipped_when_tsl_code_absent(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("battery_percentage")]
        device = MagicMock(device_name="Test")
        sensors = create_sensors_for_device_helper(MagicMock(), "key", device, tsl)
        assert not any(s.entity_description.key == "battery_pack" for s in sensors)

    def test_battery_power_created_when_no_tsl(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        device = MagicMock(device_name="Test")
        sensors = create_sensors_for_device_helper(MagicMock(), "key", device, tsl=None)
        assert any(s.entity_description.key == "battery_pack" for s in sensors)
