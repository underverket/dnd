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

2. Devices will automatically check for updates at a randomly selected minute between 03:00 and 04:00 local time and will download and install if a newer version is available.

### Time and overnight update recovery

- Failed WiFi or NTP attempts retry after one minute. Successful time syncs refresh daily.
- Friyay uses the running clock; it does not need an active WiFi connection after time sync.
- A check with no newer firmware, or a failed update attempt, returns to the display without rebooting.
- Each device chooses a fresh random minute each night to spread firmware checks across 03:00–04:00. Random slots can overlap; they are not reserved per device.
- The update schedule is held only in RAM: no schedule file is read or written. An old `last_update_check.json`, if present, is ignored.
- If the first successful time sync after boot occurs at or after 03:00, the device waits until the following night for its first scheduled firmware check. This prevents repeated checks after an update reboot. A late WiFi recovery follows the same rule. Time sync and Friyay still operate normally.
- Failed firmware checks wait until the following night; checks missed before 04:00 do not run during the day.
- Holding the touch button for six seconds still forces a firmware download.

Previously, boot-time WiFi/NTP failures were marked as finished and never retried. Since Friyay requires a successful time sync, a failed attempt after the nightly reboot disabled Friyay until another reboot. Forced nightly downloads and a check date held only in memory could also cause repeated reboots during the update window.

Host regression tests (no Pico required):

```sh
python3 -m unittest discover -s tests -v
```

For hardware verification, upload `main.py` and `firmware.json` together. Boot with the access point unavailable, then restore it: the device should sync within the next retry cycle without a power cycle. Also verify that a same-version nightly check returns to the display, and a newer-version install only happens once that night. Serial output distinguishes WiFi timeouts from NTP failures. Friyay is active Friday 15:00 through Saturday 01:59, and does not automatically override the red Busy status.

## Limitations

- Without WiFi, time synchronization is unavailable
- Without time sync, the "FRIYAY" mode won't activate
- Without WiFi, automatic updates are disabled

## Credits

Created by Max Thimmayya - Say What Again AB
