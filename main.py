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
import neopixel
import machine
import time
import math
import json
import os


"""
┌──────────────────────────────────────────────────────────────────┐
│ CONFIGURATION AND INITIALIZATION                                 │
└──────────────────────────────────────────────────────────────────┘
"""
# State tracking for the main program / screens.
class State:
    DEFAULT = "default"
    CHARACTERS = "characters"
    POMODORO = "pomodoro"
    
    class Default:
        AVAILABLE = "available"
        BUSY = "busy"
        SOCIAL = "social"

current_state = State.DEFAULT
status_state = State.Default.AVAILABLE

# Button state tracking.
button_state = {
    "pressed": False,
    "press_start": None,
    "long_press_handled": False,
    "last_release_time": 0,
    "ignore_next_release": False
}

# Characters.
CHARACTERS_DATA = [
    {
        "id": "ghost",
        "name": "Pac-Man Ghost",
        "body": [
            (0, 2), (0, 3), (0, 4), (0, 5),
            (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
            (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
            (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
            (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
            (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
            (7, 0), (7, 2), (7, 4), (7, 6),
        ],
        "eyes": [
            (4, 2), (4, 5), (5, 2), (5, 5)
        ],
    },
    {
        "id": "invader",
        "name": "Space Invader",
        "body": [
            (0, 3), (0, 4),
            (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 0), (3, 1), (3, 3), (3, 4), (3, 6), (3, 7),
            (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
            (5, 2), (5, 5),
            (6, 1), (6, 6),
            (7, 0), (7, 7)
        ],
        "eyes": [
            (2, 2), (2, 5)
        ],
    },
    {
        "id": "smiley",
        "name": "Smiley Face",
        "body": [
            (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
            (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6),
            (6, 2), (6, 3), (6, 4), (6, 5)
        ],
        "eyes": [
            (3, 2), (3, 5)
        ],
    },
    {
        "id": "heart",
        "name": "Heart",
        "body": [
            (1, 1), (1, 2), (1, 5), (1, 6),
            (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
            (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
            (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
            (5, 2), (5, 3), (5, 4), (5, 5),
            (6, 3), (6, 4)
        ],
        "eyes": []
    },
]

# Hardware Configuration.
LED_PIN = 0
BUTTON_PIN = 10
NUM_LEDS = 64

# Timing Configuration.
FRAME_DELAY = 0.01
LONG_PRESS_TIME = 700
POMODORO_IDLE_TIMEOUT = 5000
UPDATE_CHECK_TIME = 5000
WIFI_CONNECT_ATTEMPTS = 2    # Initial attempt + 2 retries
WIFI_TIMEOUT_SECONDS = 5    # Seconds to wait before timeout

# Brightness Configuration.
BRIGHTNESS = {
    'MAIN': 0.15,             # Main brightness factor
    'BACKGROUND': 0.02,       # Background dim level
    'PREVIEW': 0.05,          # Preview brightness
    'QUARTER': 0.15,          # Quarter hour dots
    'HOUR': 0.2,              # Hour dots
    'BORDER_IDLE': 0.07,      # Idle border brightness (for pomodoro)
    'BORDER_ACTIVE': 0.4,     # Active border brightness (for pomodoro)
}

# Animation.
animation_blink_time = time.ticks_ms() + random.randint(4000, 10000)
animation_is_blinking = False
animation_blink_start_time = 0

# Unsure:
rainbow_offset = 0

# Initialize hardware.
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

"""
┌──────────────────────────────────────────────────────────────────┐
│ Characters                                                       │
└──────────────────────────────────────────────────────────────────┘
"""
def find_char_index_by_id(char_id):
    """
    Return the index of CHARACTERS_DATA whose 'id' matches 'char_id'.
    If not found, return None.
    """
    for i, cdata in enumerate(CHARACTERS_DATA):
        if cdata["id"] == char_id:
            return i
    return None

# Load the selected character from a JSON file.
def read_char_conf():
    """
    Read the saved character ID from 'char_config.json',
    find its index in CHARACTERS_DATA, and return that index.
    If anything goes wrong or ID not found, return 0.
    """
    try:
        with open("char_config.json", "r") as f:
            saved_id = json.load(f)  # e.g. "ghost", "invader", etc.
        idx = find_char_index_by_id(saved_id)
        if idx is not None:
            return idx
        else:
            return 0  # Fallback if the ID doesn't match any character
    except:
        # File missing or invalid JSON
        return 0
    
# Set the selected character.
selected_character = read_char_conf()

# Ensure the selected character is within bounds, just in case.
if selected_character < 0 or selected_character >= len(CHARACTERS_DATA):
    selected_character = 0

def get_current_character_data():
    """Return the dictionary ('body', 'eyes', etc.) for the selected character index."""
    if selected_character < 0 or selected_character >= len(CHARACTERS_DATA):
        return CHARACTERS_DATA[0]  # Fallback if out of range
    return CHARACTERS_DATA[selected_character]

# Save the selected character to a JSON file.
def save_character_config(char_index):
    """
    Saves the stable 'id' of the selected character to 'char_config.json'
    instead of the numeric index.
    """
    try:
        char_id = CHARACTERS_DATA[char_index]["id"]
        with open("char_config.json", "w") as f:
            json.dump(char_id, f)
        return True
    except Exception as e:
        print(f"Failed to save character config: {e}")
        return False

def preview_char(index):
    render_char((255, 0, 128), time.ticks_ms())  # Pink color (full red, no green, half blue)
    char_name = CHARACTERS_DATA[index]["name"]
    print(f"Character Selected: {char_name}")


def render_char(color, current_time):
    global animation_blink_time, animation_is_blinking, animation_blink_start_time
    
    # 1. Fetch the data directly from CHARACTERS_DATA
    char_data = get_current_character_data()
    character_body = char_data["body"]
    character_eyes = char_data["eyes"]
    
    # 2. Same drawing logic as before
    np.fill((0, 0, 0))
    adjusted_color = adjust_color(color)

    # Draw body
    for (row, col) in character_body:
        np[get_pixel_index(row, col)] = adjusted_color

    # 3. Handle blinking eyes if present
    if character_eyes:
        # The same blink logic you already had...
        if not animation_is_blinking and time.ticks_diff(current_time, animation_blink_time) >= 0:
            animation_is_blinking = True
            animation_blink_start_time = current_time
        
        if animation_is_blinking:
            blink_cycle = (time.ticks_diff(current_time, animation_blink_start_time) // 30)
            if blink_cycle >= 8:
                # End blink
                animation_is_blinking = False
                animation_blink_time = current_time + random.randint(4000, 10000)
                for (row, col) in character_eyes:
                    np[get_pixel_index(row, col)] = EYE_COLOR
            else:
                if blink_cycle < 2 or blink_cycle >= 6:
                    for (row, col) in character_eyes:
                        np[get_pixel_index(row, col)] = EYE_COLOR
                elif blink_cycle < 4:
                    # If you want that "bottom row of eyes" effect, keep it:
                    base_row = character_eyes[0][0]
                    for (row, col) in character_eyes:
                        if row == base_row + 1:
                            np[get_pixel_index(row, col)] = EYE_COLOR
        else:
            # Normal eyes
            for (row, col) in character_eyes:
                np[get_pixel_index(row, col)] = EYE_COLOR
    
    np.write()

EYE_COLOR = (
    int(255 * BRIGHTNESS['MAIN']), 
    int(255 * BRIGHTNESS['MAIN']), 
    int(255 * BRIGHTNESS['MAIN'])
)

def render_char_rainbow(offset, current_time=None):
    # 1. Get the current character data
    char_data = get_current_character_data()
    character_body = char_data["body"]
    character_eyes = char_data["eyes"]
    
    # 2. Clear the display
    np.fill((0, 0, 0))

    # 3. Draw rainbow body
    for row in range(8):
        row_color = wheel((offset + row * 8) % 255)
        for col in range(8):
            if (row, col) in character_body:
                np[get_pixel_index(row, col)] = row_color
    
    # 4. Eyes (if any)
    if character_eyes:
        for (row, col) in character_eyes:
            np[get_pixel_index(row, col)] = EYE_COLOR
    
    np.write()

def slide_in_char():
    ANIMATION_STEPS = 8
    STEP_DELAY = 0.05
    
    # 1. Get the current character's body & eyes:
    char_data = get_current_character_data()
    char_body = char_data["body"]
    char_eyes = char_data["eyes"]
    
    # 2. Slide-up animation
    for step in range(ANIMATION_STEPS + 1):
        np.fill((0, 0, 0))
        
        # Start from 8 rows below the visible area, move to final
        offset = ANIMATION_STEPS - step
        
        # Body
        for (row, col) in char_body:
            new_row = row + offset
            if 0 <= new_row < 8:
                np[get_pixel_index(new_row, col)] = (0, int(255 * BRIGHTNESS['MAIN']), 0)
        
        # Eyes
        for (row, col) in char_eyes:
            new_row = row + offset
            if 0 <= new_row < 8:
                np[get_pixel_index(new_row, col)] = EYE_COLOR
        
        np.write()
        time.sleep(STEP_DELAY)

"""
┌──────────────────────────────────────────────────────────────────┐
│ WIFI & UPDATE FUNCTIONS                                          │
└──────────────────────────────────────────────────────────────────┘
"""
class Spinner:
    def __init__(self, color, background_color=(0,0,0)):
        self.color = color
        self.background_color = background_color
        self.position = 0
        self.last_update = time.ticks_ms()
        self.active = False
        self.fade_level = 0
        self.fade_in = True
        
        # Configuration
        self.speed = 100  # ms per step
        self.trail_length = 3
        self.fade_speed = 0.1
        
        # Define the spinner path (clockwise square)
        self.path = []
        # Top row
        self.path.extend([(2,i) for i in range(2,6)])
        # Right side
        self.path.extend([(i,5) for i in range(3,6)])
        # Bottom row
        self.path.extend([(5,i) for i in range(4,1,-1)])
        # Left side
        self.path.extend([(i,2) for i in range(4,2,-1)])
    
    def start(self):
        self.active = True
        self.fade_level = 0
        self.fade_in = True
        self.last_update = time.ticks_ms()
    
    def stop(self):
        self.fade_in = False
    
    def update(self, np):
        if not self.active:
            return False
            
        current_time = time.ticks_ms()
        
        # Handle fading
        if self.fade_in and self.fade_level < 1.0:
            self.fade_level = min(1.0, self.fade_level + self.fade_speed)
        elif not self.fade_in:
            self.fade_level = max(0.0, self.fade_level - self.fade_speed)
            if self.fade_level == 0:
                self.active = False
                return False
        
        # Update position
        if time.ticks_diff(current_time, self.last_update) >= self.speed:
            self.position = (self.position + 1) % len(self.path)
            self.last_update = current_time
        
        # Fill all pixels with background color first
        for i in range(NUM_LEDS):
            np[i] = self.background_color
        
        # Draw trail
        for i in range(self.trail_length):
            pos = (self.position - i) % len(self.path)
            row, col = self.path[pos]
            brightness = (self.trail_length - i) / self.trail_length * self.fade_level
            
            # Blend with background color
            color = tuple(
                int(bg + (c - bg) * brightness)
                for c, bg in zip(self.color, self.background_color)
            )
            
            np[get_pixel_index(row, col)] = color
        
        np.write()
        return True
    
# Load Wi-Fi credentials from `wifi_config.py`
try:
    from wifi_config import WIFI_SSID, WIFI_PASSWORD
    print(f"🔍 Loaded Wi-Fi config - SSID: {WIFI_SSID}")
except ImportError:
    print("❌ Wi-Fi configuration not found! Please create `wifi_config.py` with `WIFI_SSID` and `WIFI_PASSWORD`.")
    WIFI_SSID = None
    WIFI_PASSWORD = None

# GitHub OTA Update Configuration
CURRENT_VERSION = "1.0.3"
GITHUB_USER = "underverket"
GITHUB_REPO = "dnd"
UPDATE_URL = f"http://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/firmware.json"

def run_update():
    """
    Attempt to connect to Wi-Fi and check for an available update.
    If found, download and install. Otherwise, do nothing.
    """
    print("🔄 Checking for updates...")
    if lan_connect():
        update_url = check_for_update()
        if update_url:
            download_and_install_update(update_url)
        else:
            print("✅ No update available.")
    else:
        print("❌ Wi-Fi connection failed, skipping update.")

def lan_connect():
    # Create spinner with blue color
    spinner = Spinner(
        color=(0, 0, int(255 * BRIGHTNESS['MAIN'])),
        background_color=(0, 0, int(255 * BRIGHTNESS['BACKGROUND']))
    )
    spinner.start()

    if not WIFI_SSID or not WIFI_PASSWORD:
        spinner.stop()
        print("❌ No Wi-Fi credentials found! Skipping Wi-Fi connection.")
        show_wifi_fail_symbol()
        return False

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)

    for attempt in range(WIFI_CONNECT_ATTEMPTS):
        wlan.disconnect()
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        attempt_start = time.ticks_ms()

        while not wlan.isconnected():
            spinner.update(np)
            
            if time.ticks_diff(time.ticks_ms(), attempt_start) > WIFI_TIMEOUT_SECONDS * 1000:
                if attempt == WIFI_CONNECT_ATTEMPTS - 1:
                    spinner.stop()
                    while spinner.update(np):
                        time.sleep(0.01)
                    show_wifi_fail_symbol()
                    return False
                print("❌ Wi-Fi connection timeout! Retrying...")
                break

        else:
            spinner.stop()
            while spinner.update(np):
                time.sleep(0.01)
            print("✅ Connected!")
            print("Network config:", wlan.ifconfig())
            return True

    return False

def check_for_update():
    """Check if there's a new firmware version while keeping animation smooth (Purple)."""
    MIN_DURATION = 2000  # 2 seconds in milliseconds
    start_time = time.ticks_ms()
    FORCE_UPDATE = False 

    # Create spinner with purple colors
    spinner = Spinner(
        color=(int(128 * BRIGHTNESS['MAIN']), 0, int(255 * BRIGHTNESS['MAIN'])),
        background_color=(int(128 * BRIGHTNESS['BACKGROUND']), 0, int(255 * BRIGHTNESS['BACKGROUND']))
    )
    spinner.start()

    try:
        # Start fetching content
        content = fetch_github_raw()
        update_url = None
        
        # Process content once
        if content:
            try:
                update_info = json.loads(content)
                print(f"🔍 Current Version: {CURRENT_VERSION}")
                print(f"🚀 Latest Version: {update_info['version']}")

                if update_info['version'] > CURRENT_VERSION or FORCE_UPDATE:
                    print("🔄 New version available!")
                    update_url = update_info['url']
                else:
                    print("✅ Already up to date!")
            except Exception as e:
                print(f"❌ Update check failed: {e}")
        
        # Keep spinner going until minimum duration
        while True:
            spinner.update(np)
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            if elapsed >= MIN_DURATION:
                break
            time.sleep(0.01)

        # Graceful shutdown of spinner
        spinner.stop()
        while spinner.update(np):
            time.sleep(0.01)
            
        return update_url

    except Exception as e:
        print(f"❌ Update check failed: {e}")
        return None

    finally:
        # Ensure clean spinner shutdown if not already done
        if spinner.active:
            spinner.stop()
            while spinner.update(np):
                time.sleep(0.01)
    
def fetch_github_raw():
    """Fetch firmware.json from GitHub."""
    try:
        print(f"🌍 Fetching firmware.json from {UPDATE_URL}...")
        response = urequests.get(UPDATE_URL, timeout=10)  # Add timeout
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

def download_and_install_update(url):
    """Download new firmware, install, and reboot (Red)."""
    
    # Define the download arrow pattern
    download_arrow = [
        "0 0 0 X X 0 0 0",
        "0 0 0 X X 0 0 0",
        "0 0 0 X X 0 0 0",
        "0 X X X X X X 0",
        "0 0 X X X X 0 0",
        "0 0 0 X X 0 0 0",
        "X 0 0 0 0 0 0 X",
        "X X X X X X X X"
    ]
    
    # Convert pattern to LED positions
    arrow_leds = []
    for row, pattern in enumerate(download_arrow):
        for col, pixel in enumerate(filter(lambda x: x != ' ', pattern)):
            if pixel == 'X':
                arrow_leds.append((row, col))

    def render_arrow(brightness_factor):
        # Set background
        background_color = (int(255 * BRIGHTNESS['BACKGROUND']), 0, 0)
        np.fill(background_color)
        
        # Ensure arrow is always brighter than background
        min_brightness = BRIGHTNESS['BACKGROUND'] * 2  # Minimum brightness is 2x background
        adjusted_brightness = min_brightness + (BRIGHTNESS['MAIN'] - min_brightness) * brightness_factor
        
        # Draw arrow
        arrow_color = (int(255 * adjusted_brightness), 0, 0)
        for row, col in arrow_leds:
            np[get_pixel_index(row, col)] = arrow_color
        
        np.write()

    try:
        print("⬇️ Downloading new firmware...")
        
        # Start with full brightness pulsing while downloading
        response = urequests.get(url)
        
        if response.status_code == 200:
            content = response.text
            response.close()

            print("💾 Saving new firmware...")
            
            # Pulse the arrow while saving
            pulse_start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), pulse_start) < 2000:  # 2 second animation
                # Calculate brightness using sine wave (adjusted to stay between 0.2 and 1.0)
                progress = time.ticks_diff(time.ticks_ms(), pulse_start) / 2000
                brightness = 0.6 + 0.4 * math.sin(progress * 2 * math.pi * 2)  # Range from 0.2 to 1.0
                render_arrow(brightness)
                time.sleep(0.01)
            
            # Save the files
            with open('main.py.new', 'w') as f:
                f.write(content)

            try:
                os.remove('main.py.bak')  # Remove previous backup if it exists
            except:
                pass

            os.rename('main.py', 'main.py.bak')
            os.rename('main.py.new', 'main.py')

            print("✅ Update successful! Rebooting...")
            
            # Final bright flash before reboot
            for brightness in range(50, 100):  # Start from 50% brightness
                render_arrow(brightness/100)
                time.sleep(0.01)
            for brightness in range(100, 49, -1):  # Only fade down to 50%
                render_arrow(brightness/100)
                time.sleep(0.01)
                
            time.sleep(0.5)
            machine.reset()

        else:
            print(f"❌ HTTP Error {response.status_code}")
            response.close()
            
            # Error indication: rapid flashing but staying visible
            for _ in range(3):
                render_arrow(1.0)
                time.sleep(0.1)
                render_arrow(0.3)  # Don't go too dim
                time.sleep(0.1)

    except Exception as e:
        print(f"❌ Update failed: {e}")
        
        # Error indication: rapid flashing but staying visible
        for _ in range(3):
            render_arrow(1.0)
            time.sleep(0.1)
            render_arrow(0.3)  # Don't go too dim
            time.sleep(0.1)

def show_wifi_fail_symbol():
    """Display a 'no WiFi' symbol in red."""
    FAIL_COLOR = (255, 0, 0)
    wifi_symbol = [
        "0 0 0 0 0 0 0 0",
        "0 0 0 X X 0 0 0",
        "0 X X X X X X 0",
        "X 0 0 0 0 0 0 X",
        "0 0 X X X X 0 0",
        "0 X 0 0 0 0 X 0",
        "0 0 0 X X 0 0 0",
        "0 0 0 0 0 0 0 0"
    ]
    
    # Convert the pattern to LED positions
    symbol_leds = []
    for row, pattern in enumerate(wifi_symbol):
        for col, pixel in enumerate(filter(lambda x: x != ' ', pattern)):
            if pixel == 'X':
                symbol_leds.append((row, col))
    
    # Fade in
    for brightness in range(51):  # 0 to 50 steps
        np.fill((0, 0, 0))
        color = adjust_color(FAIL_COLOR, BRIGHTNESS['MAIN'] * brightness/50)
        for row, col in symbol_leds:
            np[get_pixel_index(row, col)] = color
        np.write()
        time.sleep(0.01)
    
    # Hold
    time.sleep(2)
    
    # Fade out
    for brightness in range(50, -1, -1):  # 50 to 0 steps
        np.fill((0, 0, 0))
        color = adjust_color(FAIL_COLOR, BRIGHTNESS['MAIN'] * brightness/50)
        for row, col in symbol_leds:
            np[get_pixel_index(row, col)] = color
        np.write()
        time.sleep(0.01)

"""
┌──────────────────────────────────────────────────────────────────┐
│ BUTTON ACTIONS                                                   │
└──────────────────────────────────────────────────────────────────┘
"""

def handle_button_events(current_time):
    global current_state, status_state, button_state
    
    button_pressed = button.value() == 0
    
    # Button just pressed
    if button_pressed and not button_state["pressed"]:
        button_state["pressed"] = True
        button_state["press_start"] = current_time
        button_state["long_press_handled"] = False
    
    # Button is being held
    elif button_pressed and button_state["pressed"]:
        press_duration = current_time - button_state["press_start"]
        
        if press_duration >= LONG_PRESS_TIME and not button_state["long_press_handled"]:
            button_state["long_press_handled"] = True
            
            # Long press state transitions
            if current_state == State.CHARACTERS:

                # 1) Save character before exiting
                save_character_config(selected_character)
                
                # 2) Then exit char select
                button_state["ignore_next_release"] = True
                current_state = State.DEFAULT
                status_state = State.Default.AVAILABLE
                slide_in_char()
                render_char((0, 255, 0), current_time)
            
            elif current_state == State.DEFAULT:
                current_state = State.POMODORO
                pomodoro_show_intro()
                start_pomodoro_setup()
                
            elif current_state == State.POMODORO:
                current_state = State.DEFAULT
                status_state = State.Default.AVAILABLE
                slide_in_char()
                render_char((0, 255, 0), current_time)

    
    # Button just released
    elif not button_pressed and button_state["pressed"]:
        press_duration = current_time - button_state["press_start"]
        button_state["pressed"] = False
        
        if not button_state["ignore_next_release"]:
            if press_duration < LONG_PRESS_TIME:
                if current_time - button_state["last_release_time"] > 300:  # Debounce
                    handle_short_press(current_time)
        
        button_state["ignore_next_release"] = False
        button_state["last_release_time"] = current_time

def handle_short_press(current_time):
    global current_state, status_state, selected_character, pomodoro
    
    if current_state == State.CHARACTERS:
        selected_character = (selected_character + 1) % len(CHARACTERS_DATA)
        preview_char(selected_character)
        
    elif current_state == State.POMODORO:
        if pomodoro["state"] == PomodoroState.SETUP:
            increment_setup_time()
            pomodoro["idle_timer"] = current_time
        elif pomodoro["state"] == PomodoroState.ACTIVE:
            pomodoro["state"] = PomodoroState.COMPLETE
            rainbow_takeover(duration=0.5, gradient_speed=3)
            
    elif current_state == State.DEFAULT:
        # Cycle through normal mode states
        if status_state == State.Default.AVAILABLE:
            status_state = State.Default.BUSY
            render_char((255, 0, 0), current_time)
        elif status_state == State.Default.BUSY:
            status_state = State.Default.SOCIAL
        else:  # SOCIAL
            status_state = State.Default.AVAILABLE
            render_char((0, 255, 0), current_time)

# Detect button and either trigger character select or update check.
def boot_button_check():

    if button.value() == 0:

        # Display character select screen immediately.
        preview_char(selected_character)

        # While button is still held, check for update trigger
        start_time = time.ticks_ms()
        while button.value() == 0:

            # If we reach update check time, run update check.
            current_hold_time = time.ticks_diff(time.ticks_ms(), start_time)
            if current_hold_time >= UPDATE_CHECK_TIME:
                run_update()
                return False # Don't enter character select after update.
        
            time.sleep(0.05)

        # Released before 5s => return True => char selection
        return True
    
    # Button not pressed => normal mode
    return False


"""
┌──────────────────────────────────────────────────────────────────┐
│ UTILITY FUNCTIONS                                                │
└──────────────────────────────────────────────────────────────────┘
"""

# Adjust a color tuple by a brightness factor.
def adjust_color(color, brightness_factor=BRIGHTNESS['MAIN']):
    """Adjust a color tuple by a brightness factor."""
    return tuple(int(c * brightness_factor) for c in color)

# Get all border pixels in order (clockwise from top-left).
def get_border_pixels():
    pixels = []
    pixels.extend([(0, i) for i in range(8)])
    pixels.extend([(i, 7) for i in range(1, 8)])
    pixels.extend([(7, i) for i in range(6, -1, -1)])
    pixels.extend([(i, 0) for i in range(6, 0, -1)])
    return pixels

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

    return (int(r * BRIGHTNESS['MAIN']), int(g * BRIGHTNESS['MAIN']), int(b * BRIGHTNESS['MAIN']))

def animate_pixels_wave_concurrent(animations):
    """
    Run multiple wave animations concurrently.
    
    Args:
        animations: List of dicts, each containing:
            - pixels: List of (row, col) tuples
            - color: Target color tuple
            - background_color: Background color tuple
            - duration: Animation duration in ms
            - delay: Start delay in ms
            - stay_lit: Boolean to keep pixels lit
            - tail_length: Float 0.0-1.0 controlling the fade trail length (optional)
    """
    start_times = []
    current_time = time.ticks_ms()
    
    for anim in animations:
        start_times.append(current_time + anim.get('delay', 0))
    
    while True:
        current_time = time.ticks_ms()
        all_complete = True
        
        for i, anim in enumerate(animations):
            if current_time < start_times[i]:
                all_complete = False
                continue
                
            time_in_anim = time.ticks_diff(current_time, start_times[i])
            
            if time_in_anim >= anim['duration']:
                # Set final state for completed animations
                final_color = anim['color'] if anim.get('stay_lit', False) else anim['background_color']
                for row, col in anim['pixels']:
                    np[get_pixel_index(row, col)] = final_color
                continue
                
            all_complete = False
            num_pixels = len(anim['pixels'])
            wave_width = num_pixels + 2
            tail_length = anim.get('tail_length', 0.5)  # Default to 0.5 if not specified
            
            progress = time_in_anim / anim['duration']
            wave_position = progress * (num_pixels + wave_width)
            
            for j, (row, col) in enumerate(anim['pixels']):
                pixel_wave_pos = wave_position - j
                
                if anim.get('stay_lit', False) and pixel_wave_pos >= wave_width/2:
                    brightness = 1
                else:
                    if pixel_wave_pos <= 0 or pixel_wave_pos >= wave_width:
                        brightness = 0
                    else:
                        brightness = 1 - abs(1 - (pixel_wave_pos / (wave_width * tail_length)))
                        brightness = max(0, min(1, brightness))
                
                current_color = tuple(
                    int(anim['background_color'][k] + (anim['color'][k] - anim['background_color'][k]) * brightness)
                    for k in range(3)
                )
                
                np[get_pixel_index(row, col)] = current_color
        
        np.write()
        time.sleep_ms(10)
        
        if all_complete:
            break

def clear_display():
    np.fill((0, 0, 0))
    np.write()


"""
┌──────────────────────────────────────────────────────────────────┐
│ POMODORO MODE                                                    │
└──────────────────────────────────────────────────────────────────┘
"""
# Constants and State
class PomodoroState:
    SETUP = "setup"
    ACTIVE = "active"
    COMPLETE = "complete"

pomodoro = {
    "state": None,
    "duration": 15,
    "start_time": None,
    "idle_timer": None,
}

# Core State Management
def set_pomodoro_state(new_state):
    """Helper to handle state transitions"""
    pomodoro["state"] = new_state
    if new_state == PomodoroState.SETUP:
        pomodoro["duration"] = 15
        pomodoro["idle_timer"] = time.ticks_ms()
    elif new_state == PomodoroState.ACTIVE:
        pomodoro["start_time"] = time.ticks_ms()
    update_pomodoro_display()

def pomodoro_initialize(current_time):
    """Main update loop for pomodoro"""
    if pomodoro["state"] == PomodoroState.SETUP:
        update_pomodoro_display()
        if pomodoro["idle_timer"] is not None:
            idle_time = time.ticks_diff(current_time, pomodoro["idle_timer"])
            if idle_time >= POMODORO_IDLE_TIMEOUT:
                start_pomodoro()
    elif pomodoro["state"] == PomodoroState.ACTIVE:
        elapsed_ms = time.ticks_diff(current_time, pomodoro["start_time"])
        elapsed_minutes = int(elapsed_ms / (60 * 1000))
        if elapsed_minutes >= pomodoro["duration"]:
            set_pomodoro_state(PomodoroState.COMPLETE)
            rainbow_takeover(duration=0.5, gradient_speed=3)
        else:
            update_pomodoro_display()

# Actions
def start_pomodoro_setup():
    """Enter setup mode with initial 15 minutes"""
    set_pomodoro_state(PomodoroState.SETUP)

def start_pomodoro():
    """Start the actual pomodoro timer"""
    set_pomodoro_state(PomodoroState.ACTIVE)

def increment_setup_time():
    """Add 15 minutes to setup time, wrap around to 15 when max is reached"""
    if pomodoro["state"] != PomodoroState.SETUP:
        return
        
    if pomodoro["duration"] >= 5 * 60:  # If at max (5 hours), reset to 15 minutes
        pomodoro["duration"] = 15
    else:
        pomodoro["duration"] = min(pomodoro["duration"] + 15, 5 * 60)
        
    pomodoro["idle_timer"] = time.ticks_ms()
    update_pomodoro_display()

# Helper Functions
def calculate_time_segments(minutes):
    """Calculate hours and quarters for any given number of minutes"""
    if minutes <= 60:
        return {"hours": 0, "quarters": minutes // 15}
    
    hours = (minutes - 15) // 60
    remaining_minutes = minutes - (hours * 60)
    return {"hours": hours, "quarters": remaining_minutes // 15}

def get_progress_bar_pixels():
    """Return the standard progress bar pixel positions"""
    pixels = []
    for i in range(4):
        pixels.append((3, 2 + i))  # Orange dots
    for i in range(4):
        pixels.append((4, 2 + i))  # Red dots
    return pixels

# Display Functions
def pomodoro_show_intro():
    """Show introduction animation when entering pomodoro mode"""
    # Colors
    background_color = (int(255 * BRIGHTNESS['BACKGROUND']), 0, 0)
    border_color = (int(255 * BRIGHTNESS['BORDER_IDLE']), 0, 0)
    quarter_color = (int(255 * BRIGHTNESS['QUARTER']), int(50 * BRIGHTNESS['QUARTER']), 0)
    hour_color = (int(255 * BRIGHTNESS['HOUR']), 0, 0)
    
    # Fill background
    np.fill(background_color)
    np.write()
    
    # Get pixel groups
    border_pixels = get_border_pixels()
    quarter_pixels = [(3, 2 + i) for i in range(4)]
    hour_pixels = [(4, 2 + i) for i in range(4)]
    
    # Define all animations
    animations = [
        {
            'pixels': border_pixels,
            'color': border_color,
            'background_color': background_color,
            'duration': 1500,
            'delay': 0,
            'stay_lit': True
        },
        {
            'pixels': quarter_pixels,
            'color': quarter_color,
            'background_color': background_color,
            'duration': 1000,
            'delay': 400
        },
        {
            'pixels': hour_pixels,
            'color': hour_color,
            'background_color': background_color,
            'duration': 1000,
            'delay': 800
        }
    ]
    
    # Run all animations concurrently
    animate_pixels_wave_concurrent(animations)

def update_pomodoro_display():
    """Unified display function for both setup and active states"""
    display_buffer = [(int(255 * BRIGHTNESS['BACKGROUND']), 0, 0)] * NUM_LEDS
    current_ms = time.ticks_ms()
    blink_on = (current_ms % 1000) < 500
    
    # Draw border
    border_pixels = get_border_pixels()
    
    if pomodoro["state"] == PomodoroState.ACTIVE:
        elapsed_ms = time.ticks_diff(current_ms, pomodoro["start_time"])
        elapsed_minutes = int(elapsed_ms / (60 * 1000))
        remaining_minutes = max(0, pomodoro["duration"] - elapsed_minutes)
        progress_ratio = remaining_minutes / pomodoro["duration"]
        pixels_to_light = int(len(border_pixels) * progress_ratio)
        
        # Active border shows progress
        for i, (row, col) in enumerate(border_pixels):
            color = (int(255 * BRIGHTNESS['BORDER_ACTIVE']), 0, 0) if i < pixels_to_light else (int(255 * BRIGHTNESS['BACKGROUND']), 0, 0)
            display_buffer[get_pixel_index(row, col)] = color
    else:
        # Setup border is solid
        for row, col in border_pixels:
            display_buffer[get_pixel_index(row, col)] = (int(255 * BRIGHTNESS['BORDER_IDLE']), 0, 0)

    # Calculate time segments to display
    minutes = pomodoro["duration"]
    if pomodoro["state"] == PomodoroState.ACTIVE:
        minutes = remaining_minutes
    
    segments = calculate_time_segments(minutes)
    progress_pixels = get_progress_bar_pixels()

    # Display hours
    for i in range(segments["hours"]):
        display_buffer[get_pixel_index(*progress_pixels[i + 4])] = (int(255 * BRIGHTNESS['HOUR']), 0, 0)

    # Display quarters
    for i in range(segments["quarters"]):
        display_buffer[get_pixel_index(*progress_pixels[i])] = (int(255 * BRIGHTNESS['QUARTER']), int(50 * BRIGHTNESS['QUARTER']), 0)

    # Show blinking next position in setup mode
    if pomodoro["state"] == PomodoroState.SETUP and blink_on:
        next_pos = None
        if segments["hours"] < 4 and segments["quarters"] == 4:
            next_pos = progress_pixels[segments["hours"] + 4]
        elif segments["quarters"] < 4:
            next_pos = progress_pixels[segments["quarters"]]
            
        if next_pos and minutes < 300:  # Don't show preview beyond 5 hours
            display_buffer[get_pixel_index(*next_pos)] = (int(255 * BRIGHTNESS['PREVIEW']), int(50 * BRIGHTNESS['PREVIEW']), 0)

    np.fill((0, 0, 0))
    for i in range(NUM_LEDS):
        np[i] = display_buffer[i]
    np.write()

def rainbow_takeover(duration=1.5, steps=20, gradient_speed=2):
    """
    Performs a diagonal rainbow transition that grows in and continues animating
    until button press, then restarts pomodoro setup.
    """
    # Capture current display state
    initial_colors = [np[i] for i in range(NUM_LEDS)]
    rainbow_offset = 0
    step_delay = duration / steps

    # Transition phase - grow in the rainbow
    for step in range(steps + 1):
        progress = step / steps
        
        for row in range(8):
            for col in range(8):
                if row + col > progress * 15:  # Diagonal coverage
                    continue
                    
                idx = get_pixel_index(row, col)
                start_color = initial_colors[idx]
                target_color = wheel((rainbow_offset + (row + col) * 12) % 255)
                
                # Blend from current to rainbow
                np[idx] = tuple(
                    int(start + (target - start) * progress)
                    for start, target in zip(start_color, target_color)
                )
                
        np.write()
        time.sleep(step_delay)
        rainbow_offset = (rainbow_offset + gradient_speed) % 255

    # Continue rainbow animation until button press
    while True:
        if button.value() == 0:  # Button press detected
            time.sleep(0.2)  # Debounce delay
            start_pomodoro_setup()
            return
            
        rainbow_offset = (rainbow_offset + gradient_speed) % 255
        
        for row in range(8):
            for col in range(8):
                np[get_pixel_index(row, col)] = wheel(
                    (rainbow_offset + (row + col) * 12) % 255
                )
                
        np.write()
        time.sleep(FRAME_DELAY * 2)

"""
┌──────────────────────────────────────────────────────────────────┐
│ MAIN PROGRAM LOOP                                               │
└──────────────────────────────────────────────────────────────────┘
"""

if boot_button_check():
    print("🎭 Entering boot mode")

    # Show the character for immediate feedback
    current_state = State.CHARACTERS
    preview_char(selected_character)
    
    # Reset button state to prevent unwanted triggers.
    button_state["pressed"] = True
    button_state["press_start"] = time.ticks_ms()
    button_state["long_press_handled"] = False
    button_state["ignore_next_release"] = True
    
    # Wait for release
    while button.value() == 0:
        time.sleep(0.05)
else:
    # Default startup
    slide_in_char()
    render_char((0, 255, 0), time.ticks_ms())
    current_state = State.DEFAULT

try:
    while True:
        current_time = time.ticks_ms()
        handle_button_events(current_time)
        
        # If state is Pomodoro, display the Pomodoro.
        if current_state == State.POMODORO:
            pomodoro_initialize(current_time)
            
        # If state is Default, display the status
        elif current_state == State.DEFAULT:
            if status_state == State.Default.SOCIAL:
                render_char_rainbow(rainbow_offset, current_time)
                rainbow_offset = (rainbow_offset + 2) % 255
                time.sleep(FRAME_DELAY)
            else:
                color = (0, 255, 0) if status_state == State.Default.AVAILABLE else (255, 0, 0)
                render_char(color, current_time)
                time.sleep(0.05)

except KeyboardInterrupt:
    clear_display()
    print("\nProgram terminated by user")