# tests/test_split_input_power.py
"""Tests for AC/Solar split input power sensors."""

from unittest.mock import MagicMock

from custom_components.pecron.sensor import PECRON_SENSORS, PecronSensor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_props(ac_input=None, dc_input=None):
    """Create a mock DeviceProperties with ac_input and dc_input set."""
    props = MagicMock()
    props.ac_input = ac_input
    props.dc_input = dc_input
    props.total_input_power = 0
    props.total_output_power = 0
    return props


def make_sensor(desc, props):
    """Create a PecronSensor backed by a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "test_key": {
            "device": MagicMock(device_name="Test Device", product_name="F3000LFP"),
            "properties": props,
        }
    }
    device = MagicMock()
    device.device_key = "test_key"
    device.device_name = "Test Device"
    return PecronSensor(coordinator, "test_key", device, desc)


def ac_input_desc():
    return next(s for s in PECRON_SENSORS if s.key == "ac_input")


def dc_input_desc():
    return next(s for s in PECRON_SENSORS if s.key == "dc_input")


# ---------------------------------------------------------------------------
# Sensor description field tests
# ---------------------------------------------------------------------------

class TestSensorDescriptionFields:
    def test_ac_input_sensor_exists(self):
        desc = ac_input_desc()
        assert desc is not None

    def test_dc_input_sensor_exists(self):
        desc = dc_input_desc()
        assert desc is not None

    def test_ac_input_struct_key(self):
        assert ac_input_desc().struct_key == "ac_power"

    def test_dc_input_struct_key(self):
        assert dc_input_desc().struct_key == "dc_input_power"

    def test_ac_input_tsl_code(self):
        assert ac_input_desc().tsl_code == "ac_data_input_hm"

    def test_dc_input_tsl_code(self):
        assert dc_input_desc().tsl_code == "dc_data_input_hm"

    def test_ac_input_unit_is_watts(self):
        from homeassistant.const import UnitOfPower
        assert ac_input_desc().native_unit_of_measurement == UnitOfPower.WATT

    def test_dc_input_unit_is_watts(self):
        from homeassistant.const import UnitOfPower
        assert dc_input_desc().native_unit_of_measurement == UnitOfPower.WATT

    def test_ac_input_not_always_create(self):
        assert ac_input_desc().always_create is False

    def test_dc_input_not_always_create(self):
        assert dc_input_desc().always_create is False


# ---------------------------------------------------------------------------
# native_value: AC input
# ---------------------------------------------------------------------------

class TestAcInputNativeValue:
    def test_returns_int_from_string_value(self):
        props = make_props(ac_input={"ac_power": "246"})
        sensor = make_sensor(ac_input_desc(), props)
        assert sensor.native_value == 246

    def test_returns_int_not_float(self):
        props = make_props(ac_input={"ac_power": "246"})
        sensor = make_sensor(ac_input_desc(), props)
        assert isinstance(sensor.native_value, int)

    def test_truncates_float_string_to_int(self):
        props = make_props(ac_input={"ac_power": "246.9"})
        sensor = make_sensor(ac_input_desc(), props)
        assert sensor.native_value == 246

    def test_returns_none_when_ac_input_is_none(self):
        props = make_props(ac_input=None)
        sensor = make_sensor(ac_input_desc(), props)
        assert sensor.native_value is None

    def test_returns_none_when_struct_key_missing(self):
        props = make_props(ac_input={"some_other_key": "100"})
        sensor = make_sensor(ac_input_desc(), props)
        assert sensor.native_value is None

    def test_returns_none_when_value_is_invalid_string(self):
        props = make_props(ac_input={"ac_power": "not_a_number"})
        sensor = make_sensor(ac_input_desc(), props)
        assert sensor.native_value is None

    def test_returns_zero_when_value_is_zero(self):
        props = make_props(ac_input={"ac_power": "0"})
        sensor = make_sensor(ac_input_desc(), props)
        assert sensor.native_value == 0

    def test_returns_none_when_coordinator_data_is_none(self):
        props = make_props(ac_input={"ac_power": "246"})
        sensor = make_sensor(ac_input_desc(), props)
        sensor.coordinator.data = None
        assert sensor.native_value is None

    def test_returns_none_when_device_not_in_coordinator(self):
        props = make_props(ac_input={"ac_power": "246"})
        sensor = make_sensor(ac_input_desc(), props)
        sensor.coordinator.data = {}
        assert sensor.native_value is None


# ---------------------------------------------------------------------------
# native_value: DC/Solar input
# ---------------------------------------------------------------------------

class TestDcInputNativeValue:
    def test_returns_int_from_string_value(self):
        props = make_props(dc_input={"dc_input_power": "369"})
        sensor = make_sensor(dc_input_desc(), props)
        assert sensor.native_value == 369

    def test_returns_int_not_float(self):
        props = make_props(dc_input={"dc_input_power": "369"})
        sensor = make_sensor(dc_input_desc(), props)
        assert isinstance(sensor.native_value, int)

    def test_returns_none_when_dc_input_is_none(self):
        props = make_props(dc_input=None)
        sensor = make_sensor(dc_input_desc(), props)
        assert sensor.native_value is None

    def test_returns_none_when_struct_key_missing(self):
        props = make_props(dc_input={"wrong_key": "369"})
        sensor = make_sensor(dc_input_desc(), props)
        assert sensor.native_value is None

    def test_returns_none_when_value_is_invalid_string(self):
        props = make_props(dc_input={"dc_input_power": "N/A"})
        sensor = make_sensor(dc_input_desc(), props)
        assert sensor.native_value is None

    def test_returns_zero_when_no_solar(self):
        props = make_props(dc_input={"dc_input_power": "0"})
        sensor = make_sensor(dc_input_desc(), props)
        assert sensor.native_value == 0


# ---------------------------------------------------------------------------
# TSL filtering
# ---------------------------------------------------------------------------

class TestTslFiltering:
    """Verify TSL filtering creates/skips sensors correctly."""

    def _make_tsl_prop(self, code):
        p = MagicMock()
        p.code = code
        return p

    def test_ac_input_created_when_tsl_code_present(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("ac_data_input_hm")]
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl)
        keys = [s.entity_description.key for s in sensors]
        assert "ac_input" in keys

    def test_ac_input_skipped_when_tsl_code_absent(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("battery_percentage")]
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl)
        keys = [s.entity_description.key for s in sensors]
        assert "ac_input" not in keys

    def test_dc_input_created_when_tsl_code_present(self):
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        tsl = [self._make_tsl_prop("dc_data_input_hm")]
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl)
        keys = [s.entity_description.key for s in sensors]
        assert "dc_input" in keys

    def test_sensors_created_when_tsl_is_none(self):
        """Fallback: all sensors created when TSL unavailable."""
        from custom_components.pecron.sensor import create_sensors_for_device_helper
        device = MagicMock(device_name="Test")
        coordinator = MagicMock()
        sensors = create_sensors_for_device_helper(coordinator, "key", device, tsl=None)
        keys = [s.entity_description.key for s in sensors]
        assert "ac_input" in keys
        assert "dc_input" in keys
