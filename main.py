# import network
# import time
# import urequests
# import os
# import machine

# # 📌 Your Wi-Fi credentials
# SSID = "The Force"
# PASSWORD = "wonderwork"

# # 📌 GitHub Firmware Info
# CURRENT_VERSION = "1.0.1"
# FIRMWARE_JSON_URL = "http://raw.githubusercontent.com/underverket/dnd/main/firmware.json"

# def connect_wifi():
#     """ Connect to Wi-Fi """
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)
#     wlan.config(pm=0xa11140)  # Disable power-saving mode

#     # Disconnect first (fixes unstable reconnects)
#     wlan.disconnect()
#     time.sleep(1)

#     print("🔍 Connecting to Wi-Fi...")
#     wlan.connect(SSID, PASSWORD)

#     timeout = 10  # Max wait time (seconds)
#     start_time = time.time()

#     while not wlan.isconnected():
#         if time.time() - start_time > timeout:
#             print("❌ Wi-Fi connection timeout! Retrying...")
#             wlan.disconnect()
#             time.sleep(1)
#             wlan.connect(SSID, PASSWORD)
#             start_time = time.time()
#         time.sleep(1)

#     print("✅ Connected!")
#     print("Network config:", wlan.ifconfig())

# # 📌 Call function
# connect_wifi()

# def check_for_update():
#     """ Check GitHub for firmware updates """
#     try:
#         print("🔍 Fetching firmware.json from GitHub...")
#         response = urequests.get(FIRMWARE_JSON_URL)
#         if response.status_code == 200:
#             update_info = response.json()
#             response.close()

#             latest_version = update_info["version"]
#             download_url = update_info["url"]

#             print(f"📌 Current Version: {CURRENT_VERSION}")
#             print(f"📢 Latest Version: {latest_version}")

#             if latest_version > CURRENT_VERSION:
#                 print("🚀 New update available! Downloading...")
#                 return download_url
#             else:
#                 print("✅ Already up to date!")
#                 return None
#         else:
#             print(f"❌ HTTP Error: {response.status_code}")
#             response.close()
#             return None
#     except Exception as e:
#         print("❌ Update check failed:", e)
#         return None

# def download_firmware(url):
#     """ Download new firmware file """
#     try:
#         print(f"🌎 Downloading firmware from {url}...")
#         response = urequests.get(url)
#         if response.status_code == 200:
#             new_code = response.text
#             response.close()
#             return new_code
#         else:
#             print(f"❌ HTTP Error {response.status_code}")
#             response.close()
#             return None
#     except Exception as e:
#         print("❌ Download failed:", e)
#         return None

# def install_update(new_code):
#     """ Save new firmware and reboot """
#     try:
#         # Backup old firmware
#         try:
#             os.remove("main.py.bak")
#         except OSError:
#             pass  # No previous backup

#         os.rename("main.py", "main.py.bak")

#         # Write new firmware
#         with open("main.py", "w") as f:
#             f.write(new_code)

#         print("✅ Update installed! Rebooting now...")
#         time.sleep(2)

#         machine.reset()  # Reboot the Pico W

#     except Exception as e:
#         print("❌ Installation failed:", e)

# # 📌 Perform OTA Update
# update_url = check_for_update()
# if update_url:
#     new_firmware = download_firmware(update_url)
#     if new_firmware:
#         install_update(new_firmware)

# Uncomment to test local server (after running `python3 -m http.server 8080` on your PC)
# test_local_server()

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    DO NOT DISTURB - LED MATRIX CONTROLLER                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import random
import network
import urequests
import machine
import neopixel
import time
import json
import os

"""
┌──────────────────────────────────────────────────────────────────┐
│ CONFIGURATION AND INITIALIZATION                                  │
└──────────────────────────────────────────────────────────────────┘
"""

# Load Wi-Fi credentials from `wifi_config.py`
try:
    from wifi_config import WIFI_SSID, WIFI_PASSWORD
    print(f"🔍 Loaded Wi-Fi config - SSID: {WIFI_SSID}")
except ImportError:
    print("❌ Wi-Fi configuration not found! Please create `wifi_config.py` with `WIFI_SSID` and `WIFI_PASSWORD`.")
    WIFI_SSID = None
    WIFI_PASSWORD = None

# GitHub OTA Update Configuration
CURRENT_VERSION = "1.0.2"
GITHUB_USER = "underverket"
GITHUB_REPO = "dnd"
UPDATE_URL = f"http://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/firmware.json"

LED_PIN = 0
BUTTON_PIN = 10
NUM_LEDS = 64
BRIGHTNESS = 0.1
FRAME_DELAY = 0.01
LONG_PRESS_TIME = 700
BORDER_BRIGHTNESS = 0.2
POMODORO_IDLE_TIMEOUT = 5000  # 5 seconds in milliseconds

# Initialize hardware
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

"""
┌──────────────────────────────────────────────────────────────────┐
│ UPDATE FUNCTIONS                                                 │
└──────────────────────────────────────────────────────────────────┘
"""
def show_update_animation():
    """Show an animation while checking for updates."""
    # np.fill((0, 0, int(50 * BRIGHTNESS)))  # Dim blue
    np.fill((int(255 * BRIGHTNESS), int(105 * BRIGHTNESS), int(180 * BRIGHTNESS)))  # Pink (RGB: 255, 105, 180)
    np.write()

def lan_connect():
    """Connect to Wi-Fi with credentials from wifi_config.py"""
    if not WIFI_SSID or not WIFI_PASSWORD:
        print("❌ No Wi-Fi credentials found! Skipping Wi-Fi connection.")
        return False

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Disable power-saving mode

    # Ensure a clean connection
    wlan.disconnect()
    time.sleep(1)

    print("🔍 Connecting to Wi-Fi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    timeout = 10  # Max wait time (seconds)
    start_time = time.time()

    while not wlan.isconnected():
        if time.time() - start_time > timeout:
            print("❌ Wi-Fi connection timeout! Retrying...")
            wlan.disconnect()
            time.sleep(1)
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            start_time = time.time()  # Reset timeout timer
        time.sleep(1)

    if wlan.isconnected():
        print("✅ Connected!")
        print("Network config:", wlan.ifconfig())
        return True
    else:
        print("❌ Wi-Fi connection failed.")
        return False


def fetch_github_raw():
    """Fetch firmware.json from GitHub."""
    try:
        print(f"🌍 Fetching firmware.json from {UPDATE_URL}...")
        response = urequests.get(UPDATE_URL)
        if response.status_code == 200:
            content = response.text
            response.close()
            return content.strip()
        else:
            print(f"❌ HTTP Error {response.status_code}")
            response.close()
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def check_for_update():
    """Check if there's a new firmware version available."""
    try:
        content = fetch_github_raw()
        if content:
            update_info = json.loads(content)
            print(f"🔍 Current Version: {CURRENT_VERSION}")
            print(f"🚀 Latest Version: {update_info['version']}")

            if update_info['version'] > CURRENT_VERSION:
                print("🔄 New version available!")
                return update_info['url']
            print("✅ Already up to date!")
        return None
    except Exception as e:
        print(f"❌ Update check failed: {e}")
        return None

def download_and_install_update(url):
    """Download new firmware, install, and reboot."""
    try:
        print("⬇️ Downloading new firmware...")
        response = urequests.get(url)
        if response.status_code == 200:
            content = response.text
            response.close()

            print("💾 Saving new firmware...")
            with open('main.py.new', 'w') as f:
                f.write(content)

            # Backup old firmware and install new
            try:
                os.remove('main.py.bak')  # Remove previous backup if it exists
            except:
                pass

            os.rename('main.py', 'main.py.bak')
            os.rename('main.py.new', 'main.py')

            print("✅ Update successful! Rebooting...")
            time.sleep(1)
            machine.reset()

        else:
            print(f"❌ HTTP Error {response.status_code}")
            response.close()

    except Exception as e:
        print(f"❌ Update failed: {e}")

"""
┌──────────────────────────────────────────────────────────────────┐
│ UTILITY FUNCTIONS                                                │
└──────────────────────────────────────────────────────────────────┘
"""
def get_pixel_index(row, col):
    return row * 8 + col

def wheel(pos):
    """ Generate rainbow colors with lower saturation (washed-out effect). """
    pos = pos % 255
    SATURATION_FACTOR = 0.9  # 0.0 = fully gray, 1.0 = full saturation

    if pos < 85:
        r, g, b = (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        r, g, b = (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        r, g, b = (0, pos * 3, 255 - pos * 3)

    # Blend towards white (desaturate)
    white_blend = 255 * (1 - SATURATION_FACTOR)
    r = int(r * SATURATION_FACTOR + white_blend)
    g = int(g * SATURATION_FACTOR + white_blend)
    b = int(b * SATURATION_FACTOR + white_blend)

    return (int(r * BRIGHTNESS), int(g * BRIGHTNESS), int(b * BRIGHTNESS))

def fill_solid_color(color):
    adjusted_color = (
        int(color[0] * BRIGHTNESS),
        int(color[1] * BRIGHTNESS),
        int(color[2] * BRIGHTNESS)
    )
    np.fill(adjusted_color)
    np.write()

def clear_display():
    np.fill((0, 0, 0))
    np.write()

"""
┌──────────────────────────────────────────────────────────────────┐
│ SIMPLE MODE - GHOST DISPLAY                                      │
└──────────────────────────────────────────────────────────────────┘
"""

next_blink_time = time.ticks_ms() + random.randint(4000, 10000)
blink_in_progress = False
blink_start_time = 0

def show_ghost_with_blink(color, current_time):
    global next_blink_time, blink_in_progress, blink_start_time
    
    adjusted_color = (
        int(color[0] * BRIGHTNESS),
        int(color[1] * BRIGHTNESS),
        int(color[2] * BRIGHTNESS),
    )
    np.fill((0, 0, 0))
    
    # Draw ALL ghost body pixels first
    for row, col in ghost_body:
        np[get_pixel_index(row, col)] = adjusted_color
    
    # Additional body pixels where eyes are
    for row, col in ghost_eyes:
        np[get_pixel_index(row, col)] = adjusted_color
    
    # Check if it's time to start a new blink
    if not blink_in_progress and time.ticks_diff(current_time, next_blink_time) >= 0:
        blink_in_progress = True
        blink_start_time = current_time
    
    # Handle blinking
    if blink_in_progress:
        blink_cycle = (time.ticks_diff(current_time, blink_start_time) // 30)
        
        if blink_cycle >= 8:  # Blink animation finished
            blink_in_progress = False
            next_blink_time = current_time + random.randint(4000, 10000)  # Set next blink time
            # Show normal eyes
            for row, col in ghost_eyes:
                np[get_pixel_index(row, col)] = EYE_COLOR
        else:
            # Blink animation
            if blink_cycle < 2:  # 60ms - both pixels
                for row, col in ghost_eyes:
                    np[get_pixel_index(row, col)] = EYE_COLOR
            elif blink_cycle < 4:  # 60ms - bottom pixel only
                for row, col in ghost_eyes:
                    if row == 5:
                        np[get_pixel_index(row, col)] = EYE_COLOR
            elif blink_cycle < 6:  # 60ms - no pixels (closed)
                pass
            elif blink_cycle < 8:  # 60ms - bottom pixel only
                for row, col in ghost_eyes:
                    if row == 5:
                        np[get_pixel_index(row, col)] = EYE_COLOR
    else:
        # Normal eyes
        for row, col in ghost_eyes:
            np[get_pixel_index(row, col)] = EYE_COLOR
    
    np.write()

def update_rainbow_ghost_with_blink(offset, current_time):
    global next_blink_time, blink_in_progress, blink_start_time
    
    np.fill((0, 0, 0))
    
    # Draw ALL body pixels first
    for row in range(8):
        row_color = wheel((offset + row * 8) % 255)
        for col in range(8):
            if (row, col) in ghost_body:
                np[get_pixel_index(row, col)] = row_color
    
    # Additional body pixels where eyes are
    for row, col in ghost_eyes:
        row_color = wheel((offset + row * 8) % 255)
        np[get_pixel_index(row, col)] = row_color
    
    # Check if it's time to start a new blink
    if not blink_in_progress and time.ticks_diff(current_time, next_blink_time) >= 0:
        blink_in_progress = True
        blink_start_time = current_time
    
    # Handle blinking
    if blink_in_progress:
        blink_cycle = (time.ticks_diff(current_time, blink_start_time) // 30)
        
        if blink_cycle >= 8:  # Blink animation finished
            blink_in_progress = False
            next_blink_time = current_time + random.randint(4000, 10000)  # Set next blink time
            # Show normal eyes
            for row, col in ghost_eyes:
                np[get_pixel_index(row, col)] = EYE_COLOR
        else:
            # Blink animation
            if blink_cycle < 2:  # 60ms - both pixels
                for row, col in ghost_eyes:
                    np[get_pixel_index(row, col)] = EYE_COLOR
            elif blink_cycle < 4:  # 60ms - bottom pixel only
                for row, col in ghost_eyes:
                    if row == 5:
                        np[get_pixel_index(row, col)] = EYE_COLOR
            elif blink_cycle < 6:  # 60ms - no pixels (closed)
                pass
            elif blink_cycle < 8:  # 60ms - bottom pixel only
                for row, col in ghost_eyes:
                    if row == 5:
                        np[get_pixel_index(row, col)] = EYE_COLOR
    else:
        # Normal eyes
        for row, col in ghost_eyes:
            np[get_pixel_index(row, col)] = EYE_COLOR
    
    np.write()

# Ghost layout
ghost_body = [
    (0, 2), (0, 3), (0, 4), (0, 5),
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
    (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
    (4, 0), (4, 1), (4, 3), (4, 4), (4, 6), (4, 7),
    (5, 0), (5, 1), (5, 3), (5, 4), (5, 6), (5, 7),
    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
    (7, 0), (7, 2), (7, 4), (7, 6),
]
ghost_eyes = [(4, 2), (4, 5), (5, 2), (5, 5)]
EYE_COLOR = (int(255 * BRIGHTNESS), int(255 * BRIGHTNESS), int(255 * BRIGHTNESS))

def show_ghost(color):
    adjusted_color = (
        int(color[0] * BRIGHTNESS),
        int(color[1] * BRIGHTNESS),
        int(color[2] * BRIGHTNESS),
    )
    np.fill((0, 0, 0))
    for row, col in ghost_body:
        np[get_pixel_index(row, col)] = adjusted_color
    for row, col in ghost_eyes:
        np[get_pixel_index(row, col)] = EYE_COLOR
    np.write()

def update_rainbow_ghost(offset):
    np.fill((0, 0, 0))
    for row in range(8):
        row_color = wheel((offset + row * 8) % 255)
        for col in range(8):
            if (row, col) in ghost_body:
                np[get_pixel_index(row, col)] = row_color
    for row, col in ghost_eyes:
        np[get_pixel_index(row, col)] = EYE_COLOR
    np.write()

def simple_mode_show_intro():
    ANIMATION_STEPS = 8  # Number of positions to move
    STEP_DELAY = 0.05   # Time between each step
    
    # For each step of animation
    for step in range(ANIMATION_STEPS + 1):
        np.fill((0, 0, 0))  # Clear display
        
        # Calculate offset (start from 8 rows down, move to final position)
        offset = ANIMATION_STEPS - step
        
        # Draw ghost body with offset
        for row, col in ghost_body:
            new_row = row + offset
            if 0 <= new_row < 8:  # Only draw if within display bounds
                np[get_pixel_index(new_row, col)] = (0, int(255 * BRIGHTNESS), 0)
        
        # Draw ghost eyes with offset
        for row, col in ghost_eyes:
            new_row = row + offset
            if 0 <= new_row < 8:  # Only draw if within display bounds
                np[get_pixel_index(new_row, col)] = EYE_COLOR
        
        np.write()
        time.sleep(STEP_DELAY)

"""
┌──────────────────────────────────────────────────────────────────┐
│ POMODORO MODE                                                    │
└──────────────────────────────────────────────────────────────────┘
"""

# State tracking section
pomodoro_duration = 15  # start with 15 minutes
pomodoro_start_time = None
pomodoro_active = False
pomodoro_setup_mode = False
setup_duration = 15  # Start with 15 minutes
pomodoro_idle_timer = None

last_setup_duration = 15  # Track previous duration to detect changes
dot_fade_progress = 0  # Track fade progress of new dot
dot_fade_start = 0  # Track when the fade started

def start_pomodoro_setup():
    """Enter setup mode with initial 15 minutes"""
    global pomodoro_setup_mode, setup_duration, pomodoro_active, pomodoro_idle_timer
    pomodoro_setup_mode = True
    setup_duration = 15
    pomodoro_active = False
    pomodoro_idle_timer = time.ticks_ms()  # Start the idle timer
    update_setup_display()

def update_setup_display():
    global last_setup_duration, dot_fade_progress, dot_fade_start
    
    current_ms = time.ticks_ms()
    blink_on = (current_ms % 1000) < 500  # Blink every half second
    
    if setup_duration != last_setup_duration:
        # print(f"Duration changed from {last_setup_duration} to {setup_duration}")  # Debug
        dot_fade_start = current_ms
        dot_fade_progress = 0
        last_setup_duration = setup_duration  # Ensure proper tracking
    
    elapsed = time.ticks_diff(current_ms, dot_fade_start) / 1000.0
    dot_fade_progress = min(1.0, elapsed / 0.3)  # 0.3 seconds fade duration
    # print(f"Fade progress: {dot_fade_progress}")  # Debug
    
    BACKGROUND_BRIGHTNESS = 0.02
    BORDER_BRIGHTNESS = 0.2
    HOUR_BRIGHTNESS = 0.2
    QUARTER_BRIGHTNESS = 0.15
    PREVIEW_BRIGHTNESS = 0.05
    
    border_color = (
        int(255 * BORDER_BRIGHTNESS),
        0,
        0
    )
    
    display_buffer = [(
        int(255 * BACKGROUND_BRIGHTNESS),
        0,
        0
    )] * NUM_LEDS

    border_pixels = get_border_pixels()
    for row, col in border_pixels:
        display_buffer[get_pixel_index(row, col)] = border_color
    
    progress_bar_pixels = []
    for i in range(4):
        progress_bar_pixels.append((3, 2 + i))
    for i in range(4):
        progress_bar_pixels.append((4, 2 + i))
    
    total_minutes = setup_duration
    
    if total_minutes <= 60:
        quarters = total_minutes // 15
        
        for i in range(quarters):
            row, col = progress_bar_pixels[i]
            brightness_factor = dot_fade_progress if setup_duration - (i + 1) * 15 == 0 else 1.0
            display_buffer[get_pixel_index(row, col)] = (
                int(255 * QUARTER_BRIGHTNESS * brightness_factor),
                int(50 * QUARTER_BRIGHTNESS * brightness_factor),
                0
            )
        
        if quarters == 4:
            row, col = progress_bar_pixels[4]  # First red LED position
            if blink_on:
                display_buffer[get_pixel_index(row, col)] = (
                    int(255 * PREVIEW_BRIGHTNESS),
                    0,
                    0
                )
        elif quarters < 4:
            row, col = progress_bar_pixels[quarters]
            if blink_on:
                display_buffer[get_pixel_index(row, col)] = (
                    int(255 * PREVIEW_BRIGHTNESS),
                    int(50 * PREVIEW_BRIGHTNESS),
                    0
                )
    else:
        hours = (total_minutes - 15) // 60
        remaining_minutes = (total_minutes - (hours * 60))
        quarters = remaining_minutes // 15
        
        for i in range(hours):
            row, col = progress_bar_pixels[i + 4]
            brightness_factor = dot_fade_progress if setup_duration - ((i + 1) * 60 + 15) == 0 else 1.0
            display_buffer[get_pixel_index(row, col)] = (
                int(255 * HOUR_BRIGHTNESS * brightness_factor),
                0,
                0
            )
        
        for i in range(quarters):
            row, col = progress_bar_pixels[i]
            brightness_factor = dot_fade_progress if setup_duration - (hours * 60 + (i + 1) * 15) == 0 else 1.0
            display_buffer[get_pixel_index(row, col)] = (
                int(255 * QUARTER_BRIGHTNESS * brightness_factor),
                int(50 * QUARTER_BRIGHTNESS * brightness_factor),
                0
            )
        
        if total_minutes < 300:
            if quarters < 4:
                row, col = progress_bar_pixels[quarters]
                if blink_on:
                    display_buffer[get_pixel_index(row, col)] = (
                        int(255 * PREVIEW_BRIGHTNESS),
                        int(50 * PREVIEW_BRIGHTNESS),
                        0
                    )
            else:
                row, col = progress_bar_pixels[hours + 4]
                if blink_on:
                    display_buffer[get_pixel_index(row, col)] = (
                        int(255 * PREVIEW_BRIGHTNESS),
                        0,
                        0
                    )
    
    for i in range(NUM_LEDS):
        np[i] = display_buffer[i]
    np.write()

def increment_setup_time():
    """Add 15 minutes to setup time"""
    global setup_duration, pomodoro_idle_timer
    if setup_duration >= 5 * 60:  # If we're at max time (5 hours)
        return  # Don't increment further
    setup_duration = min(setup_duration + 15, 5 * 60)
    pomodoro_idle_timer = time.ticks_ms()  # Reset idle timer
    update_setup_display()


def get_border_pixels():
    """Get all border pixels in order (clockwise from top-left)"""
    pixels = []
    # Top edge
    pixels.extend([(0, i) for i in range(8)])
    # Right edge
    pixels.extend([(i, 7) for i in range(1, 8)])
    # Bottom edge
    pixels.extend([(7, i) for i in range(6, -1, -1)])
    # Left edge
    pixels.extend([(i, 0) for i in range(6, 0, -1)])
    return pixels

def update_pomodoro_display(elapsed_minutes):
    """Update the display with remaining time visualization"""
    global pomodoro_duration  # Ensure we use the correct duration
    
    BACKGROUND_BRIGHTNESS = 0.02
    BORDER_BRIGHTNESS = 0.2
    HOUR_BRIGHTNESS = 0.2
    QUARTER_BRIGHTNESS = 0.15
    
    display_buffer = [(
        int(255 * BACKGROUND_BRIGHTNESS),
        0,
        0
    )] * NUM_LEDS

    border_pixels = get_border_pixels()
    total_border_pixels = len(border_pixels)
    minutes_remaining = max(0, pomodoro_duration - elapsed_minutes)  # Ensure valid range
    progress_ratio = minutes_remaining / pomodoro_duration if pomodoro_duration > 0 else 0
    pixels_to_light = int(total_border_pixels * progress_ratio)
    
    for i in range(pixels_to_light):
        row, col = border_pixels[i]
        display_buffer[get_pixel_index(row, col)] = (
            int(255 * BORDER_BRIGHTNESS),
            0,
            0
        )
    
    progress_bar_pixels = []
    for i in range(4):
        progress_bar_pixels.append((3, 2 + i))  # Orange dots (15-min segments)
    for i in range(4):
        progress_bar_pixels.append((4, 2 + i))  # Red dots (1-hour segments)
    
    total_minutes = pomodoro_duration - elapsed_minutes
    
    if total_minutes <= 60:
        quarters_remaining = (total_minutes + 14) // 15  # Ensure full 15-minute intervals
        for i in range(quarters_remaining):
            row, col = progress_bar_pixels[i]
            display_buffer[get_pixel_index(row, col)] = (
                int(255 * QUARTER_BRIGHTNESS),
                int(50 * QUARTER_BRIGHTNESS),
                0
            )
    else:
        hours_remaining = total_minutes // 60  # Ensure full hour intervals
        remaining_minutes = total_minutes % 60
        quarters_remaining = (remaining_minutes + 14) // 15  # Ensure full 15-minute intervals
        
        for i in range(hours_remaining):
            row, col = progress_bar_pixels[i + 4]  # First row is for hours
            display_buffer[get_pixel_index(row, col)] = (
                int(255 * HOUR_BRIGHTNESS),
                0,
                0
            )
        
        for i in range(quarters_remaining):
            row, col = progress_bar_pixels[i]  # Second row is for quarters
            display_buffer[get_pixel_index(row, col)] = (
                int(255 * QUARTER_BRIGHTNESS),
                int(50 * QUARTER_BRIGHTNESS),
                0
            )
    
    for i in range(NUM_LEDS):
        np[i] = display_buffer[i]
    np.write()

def show_rainbow_takeover():
    """Gradually replace the screen with a diagonal moving rainbow effect and keep animating indefinitely until button press."""
    total_fade_time = 1.5  # Total duration for full effect
    row_fade_time = 0.5  # How long each row takes to fade in
    fade_steps = 20  # More steps = smoother fade
    gradient_shift_speed = 2  # Slower shifting speed for a more subtle animation

    # Capture the current screen state before applying the rainbow effect
    previous_colors = [np[i] for i in range(NUM_LEDS)]

    # Start transition, using a starting offset that will continue in animation
    rainbow_offset = 0  

    for step in range(fade_steps + 1):
        for row in range(8):
            for col in range(8):
                if row + col > (step / fade_steps) * 15:  # Ensure full diagonal coverage
                    continue  # Skip pixels that haven't started transitioning

                # Get previous color of the pixel
                prev_color = previous_colors[get_pixel_index(row, col)]
                # Get the rainbow color at this frame
                target_color = wheel((rainbow_offset + (row + col) * 12) % 255)

                # Blend gradually between previous color and the target rainbow color
                fade_factor = step / fade_steps  # Progress from 0 → 1
                blended_color = (
                    int(prev_color[0] + (target_color[0] - prev_color[0]) * fade_factor),
                    int(prev_color[1] + (target_color[1] - prev_color[1]) * fade_factor),
                    int(prev_color[2] + (target_color[2] - prev_color[2]) * fade_factor),
                )

                np[get_pixel_index(row, col)] = blended_color

        np.write()
        time.sleep(row_fade_time / fade_steps)  # Smooth per-row fade timing

        # Ensure the animation picks up exactly where the transition left off
        rainbow_offset = (rainbow_offset + gradient_shift_speed) % 255  

    # Now start the moving gradient animation (picking up from the same offset)
    # print("[DEBUG] Rainbow Takeover: Transition complete, entering loop...")

    while True:
        # Check if the button is pressed to **exit**
        if button.value() == 0:  # Button press detected
            # print("[DEBUG] Button Pressed: Restarting Pomodoro Setup...")
            time.sleep(0.2)  # Debounce delay
            start_pomodoro_setup()
            return  # Exit the rainbow loop and restart setup

        # Continue shifting from where the transition ended
        rainbow_offset = (rainbow_offset + gradient_shift_speed) % 255  
        for row in range(8):
            for col in range(8):
                raw_color = wheel((rainbow_offset + (row + col) * 12) % 255)
                np[get_pixel_index(row, col)] = raw_color

        np.write()
        time.sleep(FRAME_DELAY * 2)  # Slower animation

def start_pomodoro():
    global pomodoro_active, pomodoro_start_time, pomodoro_duration
    pomodoro_active = True
    pomodoro_start_time = time.ticks_ms()
    
    # Ensure the pomodoro duration reflects the selected setup time
    pomodoro_duration = setup_duration
    # print(f"Pomodoro started with duration: {pomodoro_duration} minutes")  # Debugging output
    
    update_pomodoro_display(0)  # Initial display update

def get_border_segments():
    border = {
        'top': [(0, i) for i in range(8)],
        'right': [(i, 7) for i in range(8)],
        'bottom': [(7, i) for i in range(7, -1, -1)],
        'left': [(i, 0) for i in range(7, -1, -1)]
    }
    return border

def show_animated_border(color):
    # Set the dim red background first
    BACKGROUND_BRIGHTNESS = 0.02
    background_color = (
        int(255 * BACKGROUND_BRIGHTNESS),
        0,
        0
    )
    np.fill(background_color)
    np.write()
    
    # Animation parameters
    FADE_TIME = 0.4
    START_OFFSET = 0.04
    DOT_FADE_TIME = 0.3
    DOT_START_DELAY = 0.1
    DOT_SPACING = 0.1
    
    # Calculate final border color once
    final_border_color = (
        int(255 * BORDER_BRIGHTNESS),
        0,
        0
    )
    
    # Define dot positions and colors
    orange_dots = [(3, 2 + i) for i in range(4)]
    red_dots = [(4, 2 + i) for i in range(4)]
    
    QUARTER_BRIGHTNESS = 0.15
    HOUR_BRIGHTNESS = 0.2
    
    orange_color = (
        int(255 * QUARTER_BRIGHTNESS),
        int(50 * QUARTER_BRIGHTNESS),
        0
    )
    red_color = (
        int(255 * HOUR_BRIGHTNESS),
        0,
        0
    )
    
    # Setup border animation
    border = get_border_segments()
    continuous_border = []
    continuous_border.extend(border['top'])
    continuous_border.extend(border['right'])
    continuous_border.extend(border['bottom'])
    continuous_border.extend(border['left'])
    
    # Start times for border
    border_start_times = {}
    current_time = time.ticks_ms()
    for i, (row, col) in enumerate(continuous_border):
        border_start_times[get_pixel_index(row, col)] = current_time + int(i * START_OFFSET * 1000)
    
    # Start times for dots
    dot_start_time = current_time + int(DOT_START_DELAY * 1000)
    dot_start_times = {}
    for i in range(4):
        dot_start_times[get_pixel_index(*orange_dots[i])] = dot_start_time + int(i * DOT_SPACING * 1000)
        dot_start_times[get_pixel_index(*red_dots[i])] = dot_start_time + int((i + 4) * DOT_SPACING * 1000)
    
    # Calculate animation end time
    border_end_time = border_start_times[get_pixel_index(*continuous_border[-1])] + int(FADE_TIME * 1000)
    dot_end_time = max(dot_start_times.values()) + int((DOT_FADE_TIME * 2) * 1000)
    end_time = max(border_end_time, dot_end_time)
    
    while time.ticks_ms() < end_time:
        current_time = time.ticks_ms()
        
        # Animate border
        for row, col in continuous_border:
            pixel_index = get_pixel_index(row, col)
            pixel_start_time = border_start_times[pixel_index]
            
            if current_time >= pixel_start_time:
                elapsed = time.ticks_diff(current_time, pixel_start_time) / 1000.0
                progress = min(1.0, elapsed / FADE_TIME)
                
                current_color = (
                    int(final_border_color[0] * progress),
                    0,
                    0
                )
                np[pixel_index] = current_color
        
        # Animate dots
        for i in range(4):
            # Animate orange dots
            orange_pixel = get_pixel_index(*orange_dots[i])
            orange_start = dot_start_times[orange_pixel]
            if current_time >= orange_start:
                elapsed = time.ticks_diff(current_time, orange_start) / 1000.0
                if elapsed <= DOT_FADE_TIME:
                    # Fade in from background
                    progress = elapsed / DOT_FADE_TIME
                    current_color = (
                        int(background_color[0] + (orange_color[0] - background_color[0]) * progress),
                        int(background_color[1] + (orange_color[1] - background_color[1]) * progress),
                        int(background_color[2] + (orange_color[2] - background_color[2]) * progress)
                    )
                    np[orange_pixel] = current_color
                elif elapsed <= DOT_FADE_TIME * 2:
                    # Fade out to background
                    progress = (elapsed - DOT_FADE_TIME) / DOT_FADE_TIME
                    current_color = (
                        int(orange_color[0] + (background_color[0] - orange_color[0]) * progress),
                        int(orange_color[1] + (background_color[1] - orange_color[1]) * progress),
                        int(orange_color[2] + (background_color[2] - orange_color[2]) * progress)
                    )
                    np[orange_pixel] = current_color
                else:
                    np[orange_pixel] = background_color
            
            # Animate red dots
            red_pixel = get_pixel_index(*red_dots[i])
            red_start = dot_start_times[red_pixel]
            if current_time >= red_start:
                elapsed = time.ticks_diff(current_time, red_start) / 1000.0
                if elapsed <= DOT_FADE_TIME:
                    # Fade in from background
                    progress = elapsed / DOT_FADE_TIME
                    current_color = (
                        int(background_color[0] + (red_color[0] - background_color[0]) * progress),
                        int(background_color[1] + (red_color[1] - background_color[1]) * progress),
                        int(background_color[2] + (red_color[2] - background_color[2]) * progress)
                    )
                    np[red_pixel] = current_color
                elif elapsed <= DOT_FADE_TIME * 2:
                    # Fade out to background
                    progress = (elapsed - DOT_FADE_TIME) / DOT_FADE_TIME
                    current_color = (
                        int(red_color[0] + (background_color[0] - red_color[0]) * progress),
                        int(red_color[1] + (background_color[1] - red_color[1]) * progress),
                        int(red_color[2] + (background_color[2] - red_color[2]) * progress)
                    )
                    np[red_pixel] = current_color
                else:
                    np[red_pixel] = background_color
        
        np.write()
        time.sleep(0.01)

    # Ensure final state is correct
    for row, col in continuous_border:
        np[get_pixel_index(row, col)] = final_border_color
    np.write()

def pomodoro_mode_show_intro():
    show_animated_border((255, 0, 0))
    time.sleep(0.3)
    # clear_display()
"""
┌──────────────────────────────────────────────────────────────────┐
│ MAIN PROGRAM LOOP                                               │
└──────────────────────────────────────────────────────────────────┘
"""
# State tracking
mode = 0
is_pomodoro_mode = False
last_press_time = 0
button_down_time = None
rainbow_active = False
rainbow_offset = 0
long_press_handled = False

def initialize_with_timeout():
    """Initialize Wi-Fi and check for updates before starting the main loop."""
    print(f"🔵 Starting LED Matrix Controller v{CURRENT_VERSION}")
    
    show_update_animation()

    try:
        lan_connect()  # Connect to Wi-Fi
        
        # Try to fetch update info
        update_url = check_for_update()
        
        if update_url:
            download_and_install_update(update_url)
    except Exception as e:
        print(f"❌ Initialization error: {e}")
    
    clear_display()
    print("🎭 Starting LED animations...")

# Run initialization sequence
initialize_with_timeout()

# Show initial intro
simple_mode_show_intro()
show_ghost((0, 255, 0))  # Start with green ghost


try:
    while True:
        current_time = time.ticks_ms()
        
        # Button press detection
        if button.value() == 0:  # Button is pressed
            if button_down_time is None:  # Button was just pressed
                button_down_time = current_time
                long_press_handled = False
            elif current_time - button_down_time >= LONG_PRESS_TIME and not long_press_handled:
                # Long press only switches between modes now
                long_press_handled = True
                if not is_pomodoro_mode:
                    rainbow_active = False
                    is_pomodoro_mode = True
                    pomodoro_mode_show_intro()
                    start_pomodoro_setup()
                else:
                    # Exit pomodoro mode
                    is_pomodoro_mode = False
                    pomodoro_active = False
                    pomodoro_setup_mode = False
                    mode = 0  # Set to mode 0 (green ghost) instead of 1
                    simple_mode_show_intro()
                    show_ghost((0, 255, 0))  # Show green ghost after intro
        else:  # Button is released
            if button_down_time is not None:
                press_duration = current_time - button_down_time
                
                if press_duration < LONG_PRESS_TIME and not long_press_handled:
                    if current_time - last_press_time > 300:  # Debounce check
                        if is_pomodoro_mode:
                            if pomodoro_setup_mode:
                                increment_setup_time()
                                pomodoro_idle_timer = current_time
                            elif pomodoro_active:
                                pomodoro_active = False
                                # print("[DEBUG] Pomodoro cancelled! Triggering rainbow takeover...")
                                show_rainbow_takeover()
                        else:
                            mode = (mode + 1) % 3
                            if mode == 0:
                                rainbow_active = False
                                show_ghost_with_blink((0, 255, 0), current_time)  # Green ghost
                            elif mode == 1:
                                rainbow_active = False
                                show_ghost_with_blink((255, 0, 0), current_time)  # Red ghost
                            elif mode == 2:
                                rainbow_active = True    # Rainbow ghost
                        last_press_time = current_time
                
                button_down_time = None

        # Handle ongoing animations/updates
        if is_pomodoro_mode:
            if pomodoro_setup_mode:
                update_setup_display()  # Continuously update setup display to show blinking
                
                # Check idle timer
                if pomodoro_idle_timer is not None:
                    idle_time = time.ticks_diff(current_time, pomodoro_idle_timer)
                    remaining_time = (POMODORO_IDLE_TIMEOUT - idle_time) / 1000
                    # print(f"Inactive: {remaining_time:.1f} seconds remaining")  # Debug output
                    
                    if idle_time >= POMODORO_IDLE_TIMEOUT:
                        # print("Idle timeout reached - Starting pomodoro!")
                        pomodoro_setup_mode = False
                        start_pomodoro()
                time.sleep(0.05)

            elif pomodoro_active:
                current_ms = time.ticks_ms()
                elapsed_ms = time.ticks_diff(current_ms, pomodoro_start_time)
                elapsed_minutes = int(elapsed_ms / (60 * 1000))  # Convert ms to minutes
                # elapsed_minutes = int(elapsed_ms / 1000)  # Convert seconds
                if elapsed_minutes >= pomodoro_duration:
                    # Timer finished
                    pomodoro_active = False
                    # print("[DEBUG] Timer Finished! Triggering rainbow takeover...")
                    show_rainbow_takeover()
                else:
                    update_pomodoro_display(elapsed_minutes)

        elif mode == 2 and rainbow_active:
            update_rainbow_ghost_with_blink(rainbow_offset, current_time)
            rainbow_offset = (rainbow_offset + 2) % 255
            time.sleep(FRAME_DELAY)
        elif not rainbow_active:
            # Update static ghosts for blinking
            if mode == 0:
                show_ghost_with_blink((0, 255, 0), current_time)
            elif mode == 1:
                show_ghost_with_blink((255, 0, 0), current_time)
            time.sleep(0.05)

except KeyboardInterrupt:
    clear_display()
    print("\nProgram terminated by user")