# Pecron Home Assistant Integration

A Home Assistant community integration for Pecron portable power stations. Monitor and control your devices with real-time data and automation capabilities.

## Features

- **Device Control** - Turn AC and DC outputs on/off directly from Home Assistant
- **Real-time Monitoring** - Battery percentage, input/output power, and device status
- **Multi-device Support** - Manage multiple Pecron stations from one account
- **Smart Entity Discovery** - Automatically creates only the entities your device supports
- **Advanced Control Service** - `pecron.set_property` for controlling any writable device property
- **Configurable Refresh Rate** - Adjust polling interval (1-60 minutes)
- **Multi-region Support** - US, EU, and CN regions
- **Automation Ready** - Create complex automations based on battery level, power usage, etc.

## How It Works

This integration communicates with your Pecron device through **Pecron's cloud API** — the same backend used by the official Pecron mobile app. It does **not** connect directly to the device over your local network or Bluetooth.

**What this means:**
- Your Pecron device must be connected to WiFi and registered in the Pecron app
- You use the same email/password credentials as the Pecron app
- Home Assistant polls the cloud API at a configurable interval (1-60 minutes) for status updates
- Device commands (e.g., turning AC/DC on/off) are sent through the cloud API
- An active internet connection is required for both Home Assistant and the Pecron device

**Regional endpoints:**
- **US** (default): `iot-api.landecia.com`
- **EU**: `iot-api.acceleronix.io`
- **CN**: `iot-api.quectelcn.com`

## Installation

### Via HACS (this fork)

1. Go to **HACS** → **Integrations** → click the **⋮** menu (top right) → **Custom repositories**
2. Add `https://code.brockh.at/Tekchip/ha-pecron` as category **Integration**
3. Search for **Pecron** in HACS and click **Download**
4. Restart Home Assistant
5. Go to **Settings** → **Devices & Services** → **Create Integration**
6. Search for **Pecron**

> **Note:** To install the original upstream version instead, add `https://github.com/jsight/ha-pecron` as the custom repository URL.

### Manual

```bash
git clone https://code.brockh.at/Tekchip/ha-pecron.git
cp -r ha-pecron/custom_components/pecron ~/.homeassistant/custom_components/
# Restart Home Assistant
```

## Configuration

Add via the UI:
1. **Settings** → **Devices & Services** → **Create Integration**
2. Select **Pecron**
3. Enter:
   - Email
   - Password
   - Region (US, EU, or CN)
   - (Optional) Custom refresh interval

## Entities

The integration creates the following entities for each device:

### Switches
- **AC Output** - Control AC power output (on/off)
- **DC Output** - Control DC power output (on/off)

### Selects
- **AC Charge Speed** - Control AC charging power level (0%, 25%, 50%, 75%, 100%)

### Sensors
- **Battery Percentage** - Current battery level (%)
- **Input Power** - Total power being drawn from input sources (W)
- **AC Input Power** - Power from AC/shore power input (W)
- **Solar Input Power** - Power from solar/PV input (W)
- **Output Power** - Total power being output (W)
- **Time to Full** - Estimated time until battery is fully charged (minutes)
- **Time to Empty** - Estimated time until battery is depleted (minutes)
- **PV Generation (Session / Total)** - Solar energy generated this session and all-time (kWh)
- **AC Charge (Session / Total)** - Energy charged from AC/shore power (kWh)
- **DC Output (Session / Total)** - Energy discharged via DC output (kWh)
- **AC Output (Session / Total)** - Energy discharged via AC output (kWh)

### Binary Sensors
- **UPS Mode** - Whether UPS mode is active
- **Online** - Device connectivity status

*Note: Actual entities vary by device model. The integration uses TSL (Thing Specification Language) to discover and create only the entities your specific device supports.*

## Services

### `pecron.set_property`

Advanced service for controlling any writable device property.

**Parameters:**
- `device_id` (required) - The Pecron device to control
- `property_code` (required) - The property code to set (e.g., `ac_switch`, `dc_switch`)
- `value` (required) - The value to set (type depends on property)

**Example:**
```yaml
service: pecron.set_property
data:
  device_id: 1234567890abcdef
  property_code: "ac_switch"
  value: true
```

**Automation Example:**
```yaml
automation:
  - alias: "Turn off AC when battery low"
    trigger:
      - platform: numeric_state
        entity_id: sensor.pecron_battery_percentage
        below: 20
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.pecron_ac_output
```

## Requirements

- Home Assistant 2024.1 or later
- Python 3.11+

## Issues & Support

For bugs, feature requests, or questions, please open an issue on GitHub.

## Disclaimer

This integration is not affiliated with or endorsed by Pecron. It uses the unofficial API which was reverse-engineered from the Pecron Android app. Use at your own risk.

## License

MIT
