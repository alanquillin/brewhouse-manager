# Managing Plaato Keg Devices

This guide covers how to use the Plaato Keg management interface to set up, configure, and monitor your Plaato Keg devices using the native integration.

## Prerequisites

- Native Plaato Keg integration must be enabled in your configuration. See [Tap Monitor Configuration](../configs.md#plaato-keg-native-integration) for setup details.
- Admin access is required to manage Plaato Keg devices
- Access the management interface at: `/manage/plaato_kegs`

## Overview

The Plaato Keg management interface provides a complete solution for:
- Setting up new Plaato Keg devices
- Monitoring device status and connectivity
- Configuring device settings (mode, units, calibration)
- Managing multiple devices from a single dashboard

## Device List View

The main view displays all registered Plaato Keg devices in a sortable table with the following information:

### Device Information Columns

| Column | Description |
|--------|-------------|
| **Name** | The friendly name assigned to the device |
| **Device ID** | Unique identifier for the device |
| **Connected** | Connection status indicator (green checkmark = online, X = offline) |
| **Beer Remaining** | Current beer level as percentage and volume/weight |
| **Mode** | Operating mode: Beer or CO2 |
| **Unit Details** | Unit system (US/Metric) and mode (Volume/Weight) |
| **Firmware** | Current firmware version |
| **WiFi Strength** | Signal strength indicator with visual icon |
| **Last Update** | Timestamp of last data received from device (corresponds to `lastUpdatedOn` in the API) |
| **Actions** | Quick action buttons (Configure, Setup, Delete) |

**Note:** The Plaato Keg integration supports online status reporting. The API provides an `online` field indicating real-time connectivity and a `lastUpdatedOn` timestamp showing when data was last received.

### Device List Actions

- **Setup New Device**: Opens the setup wizard to add a new device
- **Refresh**: Reloads the device list
- **Sort**: Click any column header to sort by that field
- **Configure** (edit icon): Opens device configuration panel
- **Setup** (settings icon): Opens setup wizard for unconfigured devices
- **Delete** (trash icon): Removes the device from the system

## Setting Up a New Device

The device setup process involves three main steps:

### Step 1: Create Device Entry

1. Click the **Setup New Device** button
2. Enter a descriptive name for your device (e.g., "Taproom Keg 1", "Home Bar Keg")
3. Click **Submit**
4. A unique device ID will be generated automatically

**Tip:** Choose descriptive names that help you identify which physical keg each device is monitoring.

### Step 2: Put Device in Setup Mode

1. Ensure your Plaato Keg is plugged into power
2. Locate the magnetic reset key (found on the bottom of the unit)
3. Place the reset key in the reset slot on the device
4. Hold the magnet in place for approximately 3-5 seconds until the lights start flashing
5. The flashing lights indicate the device is now in setup mode
6. The device will create its own WiFi access point (AP)
7. On your computer/mobile device, connect to the Plaato WiFi network
   - Network name will be something like: `Plaato-XXXXX` or `PlaatoKeg-XXXXX`
   - No password is required for the setup WiFi

**Important:** Do not disconnect from the Plaato device's WiFi network until Step 3 is complete.

### Step 3: Configure WiFi on Device

1. While connected to the Plaato WiFi network, enter your home/brewery WiFi credentials:
   - **WiFi SSID**: Your network name
   - **WiFi Password**: Your network password
2. Click the **Configure Device** button
3. A popup window will open and send the configuration to the device
4. Look for a success message: `{"status":"ok","msg":"Configuration saved"}`
5. The popup should close automatically once configuration is verified
6. The device will disconnect you from its WiFi and connect to your network
7. Wait a few seconds for the device to appear online in the device list

**Troubleshooting:** If the device doesn't appear online after 20 seconds:
- Verify your WiFi credentials are correct
- Check that the device is within range of your WiFi network
- Ensure your WiFi network is 2.4GHz (Plaato devices do not support 5GHz)
- Try the setup process again

## Configuring Device Settings

Click the **Configure** (edit icon) button next to any device to access its configuration panel.

### Device Settings

#### Name
- Update the friendly name for the device
- Click **Save** to apply changes
- Names are for display purposes only and don't affect device operation

### Device Mode

Choose the appropriate mode for what you're monitoring:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Beer** | Monitors beer/liquid in keg | Standard keg monitoring |
| **CO2** | Monitors CO2 tank | Track CO2 tank levels |

- Changes take effect immediately
- Device will refresh its display to show appropriate measurements
- The device must be connected to change this setting

### Unit Configuration

Configure how the device displays measurements:

#### Unit Type
| Type | Description | Measurements |
|------|-------------|--------------|
| **US** | Imperial units | Gallons, pounds, Fahrenheit |
| **Metric** | Metric units | Liters, kilograms, Celsius |

#### Unit Mode
| Mode | Description | Best For |
|------|-------------|----------|
| **Volume** | Displays liquid volume | Most common; measures liquid quantity |
| **Weight** | Displays weight | Precise measurements; useful for non-standard kegs |

**Note:** Changes to unit settings take a few seconds to propagate to the device.

### Calibration Settings

Accurate calibration ensures reliable measurements.

#### Empty Keg Weight

The weight of your empty keg (without beer/liquid):

1. Remove all liquid from the keg
2. Place the empty keg on the Plaato device
3. Note the weight displayed
4. Enter this weight in the **Empty Keg Weight** field
5. Select the appropriate unit (kg for Metric, lbs for US)
6. Click **Save**

**Why this matters:** This baseline allows the device to calculate remaining beer by subtracting the empty keg weight from the total weight.

#### Max Keg Volume

The maximum volume capacity of your keg:

1. Determine your keg size:
   - Cornelius (Corny) kegs: typically 5 gallons (19 liters)
   - Sixth Barrel: 5.16 gallons (19.5 liters)
   - Quarter Barrel: 7.75 gallons (29.3 liters)
   - Half Barrel: 15.5 gallons (58.7 liters)
   - Custom sizes: measure or check manufacturer specs
2. Enter the volume in the **Max Keg Volume** field
3. Select the appropriate unit (L for Metric, gal for US)
4. Click **Save**

**Why this matters:** This allows the device to calculate the percentage of beer remaining and provide accurate volume estimates.

#### Calibration Tips

- **Perform initial calibration when first setting up each device**
- **Recalibrate if you change keg sizes**
- **Ensure kegs are properly seated on the device for accurate readings**
- **Temperature changes can affect readings slightly; recalibrate if moving between temperature extremes**

## Device Connection States

Devices can be in one of several connection states:

### Connected
- Green checkmark indicator visible
- Real-time data streaming
- All configuration changes can be made
- Recent "Last Update" timestamp

### Disconnected
- No checkmark indicator
- No recent data updates
- Configuration changes unavailable (device must be online)
- Warning message displayed in configuration panel

**If a device becomes disconnected:**
1. Check WiFi signal strength (should be above 50 for reliable connection)
2. Verify device is powered on
3. Check your WiFi network is functioning
4. Ensure device is within WiFi range
5. Try power-cycling the device
6. If issues persist, you may need to re-run the setup process

## Monitoring Device Status

### WiFi Signal Strength

Signal strength is displayed with an icon and numeric value:

| Icon | Strength | Status |
|------|----------|--------|
| 4 bars | > 90 | Excellent |
| 3 bars | 75-90 | Good |
| 2 bars | 60-75 | Fair |
| 1 bar | 50-60 | Poor |
| 0 bars | < 50 | Very Poor - Connection issues likely |

**Recommendation:** Aim for signal strength above 60 for reliable operation. If signal is weak, consider:
- Moving the device closer to your WiFi access point
- Adding a WiFi range extender
- Relocating your WiFi router

### Beer/Liquid Remaining

The device displays remaining beer in two formats:
- **Percentage**: What portion of the keg is full (0-100%)
- **Actual Amount**: Volume (gallons/liters) or weight (lbs/kg) remaining

**Empty Keg Detection:** When beer level reaches near 0%, you'll know it's time to change kegs.

### Firmware Version

Displays the current firmware version running on the device. This is informational only; firmware updates are typically handled automatically by Plaato.

## Deleting Devices

To remove a device from the system:

1. Click the **Delete** (trash icon) button next to the device
2. Confirm the deletion when prompted
3. The device will be removed from the database
4. Physical device will continue to attempt connection but won't be registered

**Important:** Deleting a device does not reset the physical hardware. If you want to re-add the same device, you can:
- Use the existing device (it will attempt to reconnect with its previous ID)
- Or perform a full reset and set up as a new device

## Best Practices

### Initial Setup
- Set up devices one at a time to avoid confusion
- Label physical devices with their assigned names
- Document which device is monitoring which tap/location
- Perform calibration immediately after setup

### Ongoing Management
- Check device status regularly
- Monitor WiFi signal strength
- Recalibrate when changing kegs or keg sizes
- Keep devices clean and free of debris
- Ensure proper keg seating on the device

### Troubleshooting Common Issues

#### Device Won't Connect During Setup
- Verify you're connected to the device's WiFi network (Plaato-XXXXX)
- Check that your browser allows popups (configuration uses a popup window)
- Ensure WiFi credentials are entered correctly
- Try a different browser if issues persist
- Make sure your WiFi is 2.4GHz (not 5GHz only)

#### Inaccurate Readings
- Recalibrate empty keg weight
- Verify max keg volume is correct for your keg size
- Ensure keg is properly seated on device (not tilted or uneven)
- Check that device is on a level surface
- Wait a few minutes after keg changes for readings to stabilize

#### Device Disconnects Frequently
- Check WiFi signal strength (should be > 50)
- Verify device power supply is secure
- Check for WiFi network issues
- Consider relocating device closer to WiFi access point
- Restart device by power cycling

#### Can't Change Configuration
- Verify device is connected (green checkmark visible)
- Check that you have admin access
- Wait for any pending operations to complete
- Refresh the device status
- If device is disconnected, troubleshoot connection first

## Additional Resources

- [Configuration Documentation](../configs.md#plaato-keg-native-integration) - Server configuration options
- [README - Plaato Keg Support](../../README.md#plaato-keg) - Integration overview
- [Plaato Support](https://plaato.io/support) - Official Plaato device support

## Support

For issues specific to the Brewhouse Manager integration:
- Check the [GitHub Issues](https://github.com/alanquillin/brewhouse-manager/issues)
- Review server logs for connection errors
- Verify configuration settings in `configs.md`

For Plaato device hardware issues:
- Refer to the official Plaato documentation
- Contact Plaato support for hardware-related problems
