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

### On-device debug report

Version 1.0.25 enables `DEBUG_MODE = True` in `main.py`. In normal status mode,
**triple-tap** to scroll a report on the matrix. Tap once to close it, or let it
finish; the previous status is restored. Set `DEBUG_MODE = False` to restore
triple-tap coffee mode. Character selection and force-update holds are unchanged.

Dots and colons use a single pixel column, with compact word spacing.
Each message scrolls at 180 ms per pixel, with a one-second blank pause between
messages. Colors identify the message type: **white** version, **cyan** weekday/time,
**orange** schedule, and **purple** update result. A **green** `SYNC RETRY` message
only appears if a later clock refresh failed while the clock is still valid.
The color identifies the section, not whether it succeeded; read `OK`, `RETRY`,
or `FAIL` for the result.

The report is a snapshot taken when you open it:

- `V 1.0.25`: firmware actually running on this device.
- `WED 23:58`, for example: local weekday and time. Only shown after successful time synchronization; there is no separate `SYNC OK` message.
- `TIME NOT SET`: no successful time sync since boot, so Friyay and scheduled updates are waiting.
- `SYNC RETRY`: a later time-sync attempt failed; the previously synchronized clock is still running and the device will retry.
- `AUTO 03:20`, for example: today's chosen firmware-check minute.
- `AUTO 03-04`: the nightly window; no pending minute is currently selected for today. Tomorrow's minute is chosen after the date changes.
- `AUTO WAIT`: waiting for a valid clock before scheduling updates.
- `UPDATE NONE`: no firmware-check result since this boot.
- `UPDATE OK`: the version check completed and no newer firmware was needed.
- `UPDATE FAIL`: the latest update attempt failed.

The report and update history stay in RAM and cause no flash writes. Installing
firmware reboots the device, clearing that history: use the displayed version to
confirm which firmware is running. Reopen the report for fresh information.

To verify overnight behavior without a computer, check the report now for a valid
time, then again tomorrow for `UPDATE OK` or `UPDATE FAIL`. If firmware was installed,
expect the new version and `UPDATE NONE` after reboot. This cannot prove the cause
of an arbitrary reboot, or guarantee a future WiFi connection.

### Hotspot status webpage

With `DEBUG_MODE = True` and `DEBUG_HOTSPOT_ENABLED = True`, triple-tapping
also starts an open hotspot in the background:

- **Network:** `DND-` followed by a six-character device ID, e.g. `DND-A1B2C3`.
- **Password:** none.
- **Duration:** five minutes from the latest debug triple-tap. Closing the report
  does not close the hotspot; starting a firmware update does.
- **Matrix:** a blue `AP DND-...` message identifies the hotspot. If startup
  fails, it shows `AP FAIL CONFIG`, `AP FAIL RADIO`, or `AP FAIL ADDRESS`
  (or `AP FAIL ID` for a device-ID error), followed by `MP x.y.z`, the
  MicroPython runtime version. Send both messages when troubleshooting.
  The same `main.py` can run on different runtime versions; OTA updates here
  replace application code, not the underlying MicroPython firmware.

Upload this `main.py`, triple-tap, and look for the network in your phone or
computer's WiFi list. Join it without a password. Your phone may offer a network
sign-in page automatically. If it does not, open **http://192.168.4.1/** in your
browser (use HTTP, not HTTPS). The server uses the AP address reported by the Pico;
if that address has been customized, use its router address from your WiFi details.

The page shows the same data and colors as the debug report: firmware,
weekday/time, update schedule, last update result, and hotspot name. A failed clock
refresh also shows `SYNC RETRY`. It also shows your current office status with
**Available** (green), **Do not disturb** (red), and **Social** (rainbow) controls.
The page checks live status every second without reloading: touch-button changes
appear on the phone, and choosing a status on the phone changes the matrix. A
phone selection closes the debug report and clears any partial triple-tap sequence.
It can end coffee mode, but cannot interrupt firmware updates, character selection,
or Pomodoro. If the hotspot disconnects, controls disable until it reconnects.

The debug cards update alongside the live status. There are no external fonts,
scripts, or internet dependencies; JavaScript must be enabled for live controls.
Opening it does not extend the five-minute hotspot lifetime; triple-tap again to
extend the session. It stops serving when the hotspot closes or an update begins.

Captive DNS and HTTP probe responses help phones offer the page automatically,
but the popup depends on the phone, DNS settings, and MicroPython networking.
Manual access to the AP address works without captive DNS. There is no internet
connection, persistent settings editor, or file browser. Reading the page and
changing office status write nothing to flash.

If an update fails, the page also shows an **Update error** card containing the
failure stage and error text. WiFi connection errors include the driver status,
interface activity, and assigned IP captured before cleanup. Reopen the hotspot
after a failure to read this information. It is held in RAM until another update
attempt or reboot; it is not a persistent log.
The whole page and server are embedded in `main.py`, so the existing OTA update
flow includes them without any extra files.

Routine time synchronization pauses while the hotspot is active and resumes
when it closes. An already synchronized clock continues running. Scheduled and
manual firmware updates take priority and close the hotspot before connecting.
After hotspot use, the next station connection disables both WiFi interfaces and
reinitializes the shared CYW43 driver before joining office WiFi. The updater allows
30 seconds per connection attempt and retries once after a driver reset. If both
attempts fail, it returns to the display without rebooting.
Set `DEBUG_HOTSPOT_ENABLED = False` to keep diagnostics without a hotspot;
`DEBUG_MODE = False` restores the original coffee triple-tap.

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
