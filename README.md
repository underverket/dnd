## Overview

This project turns your Raspberry Pi Pico 2W into a smart status display using an 8x8 LED matrix. Features include:

- Status indicators (Available, Busy, Social)
- Pomodoro timer mode
- Character display with customizable animations
- WiFi connectivity for time synchronization and OTA updates
- Special Friday celebration mode

## Hardware Requirements

- Raspberry Pi Pico 2W with RP2350 chip
- 8x8 LED Matrix
- Pushbutton switch
- Jumper wires for connections

## Wiring Instructions

Connect the components as follows:

- **LED Matrix**: 
  - GND → Pico GND
  - 3V3 → Pico 3V3
  - DATA → Pico GP0

- **Button**:
  - One terminal → Pico GP10
  - Other terminal → Pico GND

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/underverket/dnd.git
   cd dnd
   ```

2. Create a `wifi_config.py` file (not included in the repo) with your WiFi credentials:
   ```python
   WIFI_SSID = "your_wifi_name"
   WIFI_PASSWORD = "your_wifi_password"
   ```

3. Upload all files to your Pico (One time thing - after this it will automatically update):
   - `main.py`
   - `firmware.json`
   - `wifi_config.py` (your created file - remember to not include in repo)

## Usage

### Operating Modes

#### Regular Mode
- **Short press**: Cycle through status modes (Available, Busy, Social)
- **Long press**: Switch to Pomodoro mode

#### Pomodoro Mode
- **Short press**: Add 15 minutes to timer (up to 60 minutes)
- **Long press**: Return to regular mode
- After 5 seconds of inactivity, the timer starts
- Short press during active timer resets the timer

#### Special Boot Modes
- **Hold button during boot**: Enter character selection mode
  - Short press to cycle through characters
  - Long press to select and save
- **Hold button for 4+ seconds during boot**: Force firmware update

#### WiFi Features
When connected to WiFi, the device will:
- Synchronize time for accurate operation
- Enable Friday celebration mode (active Friday afternoon to Saturday morning)
- Check for firmware updates at midnight

## Project Structure

```
├── main.py            # Main application code
├── firmware.json      # Firmware version information
├── wifi_config.py     # WiFi credentials (create this manually - don't include in repo)
├── buildscripts/
│   ├── build.py       # Script to build character data
│   └── chars.py       # Character definitions in ASCII art format
```

## Adding Custom Characters

1. Edit `buildscripts/chars.py` to create or modify character designs using ASCII art
2. Run the build script to generate the optimized character data:
   ```
   cd buildscripts
   ```
   ```
   python3 build.py
   ```
3. The script will update the character data in `main.py`

## Updating the Firmware

When releasing a new version:

1. Update the version number in:
   - `main.py` (CURRENT_VERSION variable)
   - `firmware.json`

2. Devices will automatically check for updates at midnight (3:00-3:45 AM) and will download and install if a newer version is available.

## Limitations

- Without WiFi, time synchronization is unavailable
- Without time sync, the "FRIYAY" mode won't activate
- Without WiFi, automatic updates are disabled

## Credits

Created by Max Thimmayya - Say What Again AB