# Managing Tap Monitors

This guide provides an overview of tap monitor management in Brewhouse Manager, including supported tap monitor types and general configuration concepts.

## Overview

Brewhouse Manager supports various tap monitors to monitor your brewing equipment. Tap monitors provide real-time data on keg levels, temperatures, and other metrics critical to managing your brewery or taproom.

## Supported Tap Monitor Types

### Plaato Keg

The Plaato Keg is a smart keg monitoring device that tracks beer levels using weight measurements.

**Features:**
- Real-time beer level monitoring (percentage and volume/weight)
- WiFi connectivity with signal strength monitoring
- Support for both Beer and CO2 monitoring modes
- Configurable units (US/Metric) and measurement modes (Volume/Weight)
- Calibration settings for accurate readings

**Documentation:** [Plaato Keg Management Guide](./plaato-keg.md)

### Kegtron

Kegtron devices provide keg monitoring through flow measurement technology.

**Features:**
- Flow-based beer level tracking
- Multi-tap support
- WiFi connectivity
- Real-time pour tracking

**Documentation:** Coming soon

## General Tap Monitor Concepts

### Connectivity

Most tap monitors connect via WiFi to your local network. Key considerations:

- **2.4GHz Networks**: Most IoT tap monitors only support 2.4GHz WiFi networks
- **Signal Strength**: Position tap monitors within good range of your WiFi access point
- **Network Stability**: A stable network connection ensures reliable data reporting

### Calibration

Proper calibration is essential for accurate tap monitor readings:

- **Initial Calibration**: Always calibrate tap monitors during initial setup
- **Recalibration**: Recalibrate when changing keg sizes or if readings become inaccurate
- **Environmental Factors**: Temperature changes can affect readings; recalibrate if moving between temperature extremes

### Data Refresh

Tap monitors report data at regular intervals. The management interface shows:

- **Last Update**: When the tap monitor last reported data
- **Connection Status**: Whether the tap monitor is currently reachable
- **Real-time Values**: Current readings from the tap monitor

## Accessing Tap Monitor Management

Tap monitor management interfaces are available through the Brewhouse Manager admin area:

| Tap Monitor Type | Management URL |
|------------------|----------------|
| Plaato Keg | `/manage/plaato_kegs` |
| Kegtron | `/manage/kegtrons` |

**Note:** Admin access is required to manage tap monitor devices.

## Troubleshooting

### Tap Monitor Not Connecting

1. Verify the tap monitor is powered on
2. Check that your WiFi network is operational
3. Ensure the tap monitor is within range of your WiFi access point
4. Confirm the network is 2.4GHz (most tap monitors don't support 5GHz)
5. Try power-cycling the tap monitor

### Inaccurate Readings

1. Verify calibration settings are correct
2. Ensure the tap monitor is properly positioned
3. Check for environmental factors (temperature, humidity)
4. Allow time for readings to stabilize after changes

### Tap Monitor Disconnects Frequently

1. Check WiFi signal strength at the tap monitor location
2. Consider adding a WiFi range extender
3. Verify your network isn't overloaded
4. Check for interference from other devices

## Additional Resources

- [Configuration Documentation](../configs.md) - Server configuration options for tap monitors
- [Plaato Keg Guide](./plaato-keg.md) - Detailed Plaato Keg management
