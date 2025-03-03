"""
LED Matrix Controller - Example with Small State Classes
"""
import network
import urequests
import os
import machine
import neopixel
import time
import json
import ntptime
import gc

# --------------------------------------------------------------------------------
# Hardware Configuration
# --------------------------------------------------------------------------------
LED_PIN = 0
BUTTON_PIN = 10
NUM_LEDS = 64
BRIGHTNESS = 0.2

# --------------------------------------------------------------------------------
# Timing Configuration
# --------------------------------------------------------------------------------
LONG_PRESS_TIME = 700       # 0.7 seconds for long press
UPDATE_CHECK_TIME = 4000    # 4 seconds for update check
INTRO_DURATION = 1000       # 1 second for intro animations
POMODORO_SETUP_TIMEOUT = 5000  # 5 seconds before auto-starting

# Scheduled update check
SCHEDULED_UPDATE_CHECK = 60000  # 1 minute
SCHEDULED_FRIYAY_CHECK = 10000  # 1 minute

# GitHub OTA Update Configuration
FORCE_UPDATE = True  # Set this to True to force update regardless of version
WIFI_TIMEOUT_SECONDS = 10    # Seconds to wait before timeout
WIFI_CONNECT_ATTEMPTS = 2   # Initial attempt + 2 retries
WIFI_DISCONNECT_AFTER_USE = True  # Disconnect from WiFi after use
CURRENT_VERSION = "1.0.10"
GITHUB_USER = "underverket"
GITHUB_REPO = "dnd"
UPDATE_URL = f"http://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/firmware.json"

# --------------------------------------------------------------------------------
# WiFi Management
# --------------------------------------------------------------------------------
class WiFiManager:
    """Centralized WiFi connection management."""
    
    @staticmethod
    def start_connection():
        """Initialize WiFi connection process."""
        try:
            from wifi_config import WIFI_SSID, WIFI_PASSWORD
            if not WIFI_SSID or not WIFI_PASSWORD:
                raise Exception("No WiFi credentials")
                
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                return True, "Already connected"
                
            print(f"Connecting to WiFi: {WIFI_SSID}")
            wlan.active(True)
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            return True, WIFI_SSID
            
        except ImportError:
            return False, "No WiFi credentials file"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def check_connection():
        """Check current connection status."""
        wlan = network.WLAN(network.STA_IF)
        return wlan.isconnected()
    
    @staticmethod
    def disconnect():
        """Safely disconnect from WiFi."""
        if WIFI_DISCONNECT_AFTER_USE:
            try:
                wlan = network.WLAN(network.STA_IF)
                if wlan.isconnected():
                    wlan.disconnect()
                    wlan.active(False)
                    print("WiFi disconnected")
            except Exception as e:
                print(f"WiFi disconnect error: {e}")

# --------------------------------------------------------------------------------
# Base State Class
# --------------------------------------------------------------------------------
class BaseState:
    """Abstract base class for states."""
    def __init__(self, controller):
        self.controller = controller
        self.sub_state = None  # Used for cnsistent sub-state handling.
        self.entry_time = None  # Used for timing management.

    def on_enter(self, **kwargs):
        """Called when entering this state, with kwargs for flexible state transitions."""
        self.entry_time = time.ticks_ms()
    
    def on_exit(self):
        """Called when leaving this state."""
        pass
    
    def update(self, current_time):
        """Periodic update (e.g., for time-based transitions)."""
        pass
    
    def handle_short_press(self):
        """Handle short button press."""
        pass
    
    def handle_long_press(self):
        """Handle long button press."""
        pass
    
    def update_display(self):
        """Set LEDs appropriately for this state."""
        pass

    def _fill_solid_color(self, color):
        """Helper: fill display with solid color."""
        color = tuple(int(c * BRIGHTNESS) for c in color)
        self.controller.np.fill(color)
        self.controller.np.write()

    def ticks_since_entry(self):
            """Helper: get ms since state entry."""
            return time.ticks_diff(time.ticks_ms(), self.entry_time)
    
    def _get_pixel_index(self, row, col):
        """Convert row and column to LED index."""
        return row * 8 + col
    
    def _get_border_pixels(self):
        """Get all border pixels in clockwise order."""
        pixels = []
        # Top edge
        pixels.extend([(0, i) for i in range(8)])
        # Right edge
        pixels.extend([(i, 7) for i in range(1, 8)])
        # Bottom edge (right to left)
        pixels.extend([(7, i) for i in range(6, -1, -1)])
        # Left edge (bottom to top)
        pixels.extend([(i, 0) for i in range(6, 0, -1)])
        return pixels

# --------------------------------------------------------------------------------
# Character Definition and Processing
# --------------------------------------------------------------------------------
def decode_pattern_to_pixels(hex_pattern):
    """Convert hex pattern directly to pixel coordinates"""
    pixels = []
    for row in range(8):
        # Get the byte for this row
        byte = int(hex_pattern[row*2:row*2+2], 16)
        
        # Check each bit
        for col in range(8):
            if byte & (1 << (7-col)):
                pixels.append((row, col))
    return pixels

class CharacterDefinition:
    """Process compressed character definitions into pixel data"""
    @staticmethod
    def create_character(data):
            
        """Convert a character definition into processed pixel data"""
        character = {
            'id': data['id'],
            'name': data['name'],
            'pixels': []
        }
        
        # Process body pattern
        if 'body' in data:
            body_pixels = decode_pattern_to_pixels(data['body'])
            for pixel in body_pixels:
                character['pixels'].append({
                    'row': pixel[0],
                    'col': pixel[1],
                    'type': 'body'
                })
                
        # Process highlight layer
        if 'hl' in data:
            highlight_pixels = decode_pattern_to_pixels(data['hl'])
            for pixel in highlight_pixels:
                character['pixels'].append({
                    'row': pixel[0],
                    'col': pixel[1],
                    'type': 'highlight'
                })
                
        # Process shadow layer
        if 'sdw' in data:
            shadow_pixels = decode_pattern_to_pixels(data['sdw'])
            for pixel in shadow_pixels:
                character['pixels'].append({
                    'row': pixel[0],
                    'col': pixel[1],
                    'type': 'shadow'
                })
        
        # Handle custom colored pixels - list format [col, row, color]
        if 'custom' in data:
            for pixel in data['custom']:
                character['pixels'].append({
                    'row': pixel[1],      # Index 1: row
                    'col': pixel[0],      # Index 0: col
                    'type': 'fixed',
                    'color': pixel[2]     # Index 2: color
                })
        
        # Process animations - handle list format
        if 'animations' in data:
            character['animations'] = []
            for anim in data['animations']:
                # Process list format
                processed_anim = {
                    'name': anim[0],                # Index 0: name
                    'interval': anim[1],            # Index 1: interval
                    'frame_duration': anim[2],      # Index 2: frame_duration
                    'frames': [decode_pattern_to_pixels(frame) for frame in anim[3]],  # Index 3: frames
                    'color': anim[4],               # Index 4: color
                    'reverse': anim[5]              # Index 5: reverse
                }
                character['animations'].append(processed_anim)
                
        return character

class Character:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.pixels = data['pixels']
        self.rainbow_offset = 0

        # Animation handling
        self.animations = {}

        # Process animations if they exist in the data
        if 'animations' in data:
            for anim in data['animations']:
                self.animations[anim['name']] = {
                    'interval': anim['interval'],
                    'frame_duration': anim['frame_duration'],
                    'reverse': anim.get('reverse', False),
                    'color': anim.get('color', (255, 255, 255)),
                    'frames': anim['frames'],
                    'last_trigger': time.ticks_ms(),
                    'current_frame': 0,
                    'direction': 1
                }
        
    def _update_animations(self, current_time):
        """Update all animation states"""
        animation_pixels = []
        
        for anim_name, anim in self.animations.items():
            # Check time since last trigger
            time_since_trigger = time.ticks_diff(current_time, anim['last_trigger'])
            
            # If we haven't reached the interval yet, show first frame
            if time_since_trigger < anim['interval']:
                frame_pixels = anim['frames'][0]
                animation_pixels.extend([
                    {'row': pixel[0], 'col': pixel[1], 'color': anim['color']}
                    for pixel in frame_pixels
                ])
                continue
                
            # Calculate which frame to show
            animation_duration = anim['frame_duration'] * len(anim['frames'])
            time_into_interval = time_since_trigger % anim['interval']
            
            if time_into_interval < animation_duration:
                frame_number = (time_into_interval // anim['frame_duration'])
                if frame_number >= len(anim['frames']):
                    frame_number = 0
            else:
                frame_number = 0
                
            # Add current frame's pixels to animation list
            frame_pixels = anim['frames'][frame_number]
            animation_pixels.extend([
                {'row': pixel[0], 'col': pixel[1], 'color': anim['color']}
                for pixel in frame_pixels
            ])
                
        return animation_pixels

    def render(self, mode, np, brightness=0.1, row_offset=0, selection_color=None):
        """Updated render to handle animations"""
        np.fill((0, 0, 0))
        
        # Render base character first
        if selection_color:
            self._render_solid(np, mode, brightness, row_offset, selection_color)
        else:
            if mode == 'social':
                self._render_rainbow(np, brightness, row_offset)
            else:
                self._render_solid(np, mode, brightness, row_offset)
        
        # Then overlay animation pixels
        animation_pixels = self._update_animations(time.ticks_ms())
        for pixel in animation_pixels:
            new_row = pixel['row'] + row_offset
            if 0 <= new_row < 8:
                color = tuple(int(c * brightness) for c in pixel['color'])
                np[self._get_pixel_index(new_row, pixel['col'])] = color
                
        np.write()
                
    def _render_solid(self, np, mode, brightness, row_offset=0, override_color=None):
        base_colors = {
            'available': (0, 255, 0),  # Green
            'busy': (255, 0, 0),      # Red
        }
        base_color = override_color if override_color else base_colors.get(mode, (255, 255, 255))
        
        for pixel in self.pixels:
            new_row = pixel['row'] + row_offset
            if 0 <= new_row < 8:  # Only render if pixel is on screen
                color = self._process_pixel(pixel, base_color, brightness)
                np[self._get_pixel_index(new_row, pixel['col'])] = color


    def _render_rainbow(self, np, brightness, row_offset=0):

        # Set speed of rainbow effect
        self.rainbow_offset = (self.rainbow_offset + 3) % 255
        
        for pixel in self.pixels:
            new_row = pixel['row'] + row_offset
            if 0 <= new_row < 8:  # Only render if pixel is on screen
                if pixel['type'] == 'fixed':
                    color = pixel['color']
                else:
                    # Set smoothness of gradient (Lower = smoother)
                    hue = (self.rainbow_offset + (new_row + pixel['col']) * 6) % 255
                    color = self._wheel(hue)
                
                color = tuple(int(c * brightness) for c in color)
                np[self._get_pixel_index(new_row, pixel['col'])] = color

    def _process_pixel(self, pixel, base_color, brightness):
        if pixel['type'] == 'fixed':
            color = pixel['color']
        elif pixel['type'] == 'highlight':
            color = tuple(min(255, c + 40) for c in base_color)
        elif pixel['type'] == 'shadow':
            color = tuple(max(0, c - 40) for c in base_color)
        else:  # 'body'
            color = base_color
            
        return tuple(int(c * brightness) for c in color)
    
    @staticmethod
    def _wheel(pos):
        """Generate rainbow colors with softer tones."""
        # Minimum value creates the "softness" - higher = softer colors
        min_value = 10  # Try values between 50-100
        # Max value stays at 255 but the difference between min and max is smaller
        max_value = 255
        
        if pos < 85:
            return (
                min_value + int(pos * 3 * (max_value-min_value)/255), 
                min_value + int((255 - pos * 3) * (max_value-min_value)/255), 
                min_value
            )
        elif pos < 170:
            pos -= 85
            return (
                min_value + int((255 - pos * 3) * (max_value-min_value)/255), 
                min_value, 
                min_value + int(pos * 3 * (max_value-min_value)/255)
            )
        else:
            pos -= 170
            return (
                min_value, 
                min_value + int(pos * 3 * (max_value-min_value)/255), 
                min_value + int((255 - pos * 3) * (max_value-min_value)/255)
            )

    @staticmethod
    def _get_pixel_index(row, col):
        return row * 8 + col
    
# --------------------------------------------------------------------------------
# Character Definitions
# --------------------------------------------------------------------------------
# BEGIN COMPRESSED CHARACTER DATA
CHARACTERS_RAW = [
    {
        'animations': [['blink', 3000, 50, ['0000000024240000', '0000000000240000', '0000000000000000'], (255, 255, 255), False]],
        'body': '3C7EFFFFFFFFFFAA',
        'id': 'ghost_plain',
        'name': 'Plain Ghost'
    },
    {
        'animations': [['blink_heart', 7000, 50, ['0000002424000000', '0000000024000000', '0000000000000000'], (255, 255, 255), False]],
        'body': '0066FFFF7E3C1800',
        'hl': '0006030100000000',
        'id': 'heart',
        'name': 'Heart'
    },
    {
        'animations': [['blik_invader', 7000, 50, ['0000002400000000', '0000000000000000'], (255, 255, 255), False]],
        'body': '423C7EFF7E422400',
        'id': 'invader',
        'name': 'Space Invader'
    },
    {
        'animations': [['blik_invader', 7000, 50, ['006666187E7E4200', '000066187E7E4200', '000000187E7E4200'], (255, 255, 255), False]],
        'body': 'FFFFFFFFFFFFFFFF',
        'id': 'creeper',
        'name': 'Creeper'
    }
]
# END COMPRESSED CHARACTER DATA

# Process the raw definitions into our final character data
CHARACTERS_DATA = [CharacterDefinition.create_character(char) for char in CHARACTERS_RAW]

# --------------------------------------------------------------------------------
# DefaultState
# --------------------------------------------------------------------------------
class DefaultSubState:
    """Default mode states"""
    INTRO = "intro"
    AVAILABLE = "available"
    BUSY = "busy"
    SOCIAL = "social"
    FRIYAY = "friyay"
    
    # Base states that we always cycle through
    BASE_CYCLE_STATES = [AVAILABLE, BUSY, SOCIAL]
    
    # Dynamic cycle states (will be updated at runtime)
    CYCLE_STATES = BASE_CYCLE_STATES.copy()

class DefaultState(BaseState):
    """Main 'Default' state with sub-states: INTRO, AVAILABLE, BUSY, SOCIAL."""

    ANIMATION_DURATION = 600  # Total duration in milliseconds

    def __init__(self, controller):
        super().__init__(controller)
        self.sub_state = DefaultSubState.INTRO
        self.character = Character(CHARACTERS_DATA[controller.selected_character])
        self.animation_start = None

        # Initialize FRIYAY-related attributes
        self.friyay_scroll_position = 0
        self.last_scroll_time = 0
    
    def on_enter(self):
        print("Entering DefaultState / INTRO")
        self.sub_state = DefaultSubState.INTRO
        self.animation_start = time.ticks_ms()
        self.character = Character(CHARACTERS_DATA[self.controller.selected_character])
    
    def _ease_out_cubic(self, t):
        """Cubic easing function for smooth animation"""
        t = 1 - t
        return 1 - (t * t * t)
    
    def update(self, current_time):
        if self.sub_state == DefaultSubState.INTRO:
            progress = time.ticks_diff(current_time, self.animation_start) / self.ANIMATION_DURATION
            
            if progress >= 1:
                print(f"Auto: Default {DefaultSubState.INTRO} → {DefaultSubState.AVAILABLE}")
                self.sub_state = DefaultSubState.AVAILABLE
    
    def handle_short_press(self):
        if self.sub_state != DefaultSubState.INTRO:  # Don't interrupt intro
            # Find current state in cycle and move to next
            try:
                current_idx = DefaultSubState.CYCLE_STATES.index(self.sub_state)
            except ValueError:
                # If current state not in cycle (shouldn't happen), go to first state
                current_idx = -1
                
            next_idx = (current_idx + 1) % len(DefaultSubState.CYCLE_STATES)
            self.sub_state = DefaultSubState.CYCLE_STATES[next_idx]
            print(f"Short press: Default → {self.sub_state}")
    
    def handle_long_press(self):
        if self.sub_state != DefaultSubState.INTRO:  # Don't interrupt intro
            print("Long press: Default → Pomodoro INTRO")
            self.controller.switch_to(PomodoroState(self.controller))
    
    def update_display(self):
        if self.sub_state == DefaultSubState.INTRO:
            # Calculate smooth animation progress
            progress = time.ticks_diff(time.ticks_ms(), self.animation_start) / self.ANIMATION_DURATION
            if progress > 1:
                progress = 1
                
            # Apply easing function
            eased_progress = self._ease_out_cubic(progress)
            
            # Calculate row offset (8 to 0)
            row_offset = (1 - eased_progress) * 8
            
            # Render with calculated offset
            self.character.render(
                mode=DefaultSubState.AVAILABLE,
                np=self.controller.np,
                brightness=BRIGHTNESS,
                row_offset=int(row_offset)
            )
        elif self.sub_state == DefaultSubState.FRIYAY:
            # Render the scrolling "FRIYAY!" text
            self._render_scrolling_text(self.FRIYAY_TEXT, color=(255, 255, 0))  # Yellow text
        else:
            # Normal rendering
            self.character.render(
                mode=self.sub_state,
                np=self.controller.np,
                brightness=BRIGHTNESS
            )
    
    # Add these new properties
    FRIYAY_TEXT = "FRIYAY!"
    friyay_scroll_position = 0
    last_scroll_time = 0
    SCROLL_SPEED = 100  # ms between scroll steps
    
    def _render_scrolling_text(self, text, color=(255, 255, 0)):
        # First create a rainbow background
        rainbow_offset = (time.ticks_ms() // 15) % 256  # Slower color cycling
        for row in range(8):
            for col in range(8):
                # Create a diagonal rainbow pattern
                hue = (rainbow_offset + (row + col) * 8) % 256
                bg_color = Character._wheel(hue)
                # Dim background for contrast
                bg_color = tuple(int(c * BRIGHTNESS) for c in bg_color)
                pixel_index = self._get_pixel_index(row, col)
                self.controller.np[pixel_index] = bg_color

        font = {
            'F': [(0,0), (0,1), (0,2), (0,3), (1,0), (2,0), (3,0), (3,1), (4,0), (5,0)],
            'R': [(0,0), (0,1), (0,2), (0,3), (1,0), (1,3), (2,0), (2,3), (3,0), (3,1), (3,2), (4,0), (4,2), (5,0), (5,3)],
            'I': [(0,1), (1,1), (2,1), (3,1), (4,1), (5,1)],
            'Y': [(0,0), (0,4), (1,0), (1,4), (2,1), (2,2), (2,3), (3,2), (4,2), (5,2)],
            'A': [(0,1), (0,2), (0,3), (1,0), (1,4), (2,0), (2,4), (3,0), (3,1), (3,2), (3,3), (3,4), (4,0), (4,4), (5,0), (5,4)],
            '!': [(0,2), (1,2), (2,2), (3,2), (5,2)]
        }
        
        # Calculate character widths
        char_widths = {char: max(col for _, col in pixels) - min(col for _, col in pixels) + 1
                    for char, pixels in font.items()}
        
        # Total width of the text (including 1px gap between characters) plus 8px extra padding
        total_width = sum(char_widths.get(char, 0) + 1 for char in text) + 8
        
        # Update scroll position
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_scroll_time) > self.SCROLL_SPEED:
            self.friyay_scroll_position = (self.friyay_scroll_position + 1) % total_width
            self.last_scroll_time = current_time
        
        # Calculate starting position
        x_pos = 8 - self.friyay_scroll_position
        vertical_offset = 1  # Move down 1px
        
        # Make text bright white for maximum contrast
        text_color = (int(255 * BRIGHTNESS), int(255 * BRIGHTNESS), int(255 * BRIGHTNESS))
        
        # Render the text only once
        text_x_pos = x_pos
        for char in text:
            if char in font:
                min_col = min(col for _, col in font[char])
                for row, col in font[char]:
                    screen_row = row + vertical_offset
                    screen_col = text_x_pos + (col - min_col)
                    if 0 <= screen_row < 8 and 0 <= screen_col < 8:
                        pixel_index = self._get_pixel_index(screen_row, screen_col)
                        self.controller.np[pixel_index] = text_color
                text_x_pos += char_widths[char] + 1  # Add a 1px gap between characters
        
        self.controller.np.write()

# --------------------------------------------------------------------------------
# CharactersState
# --------------------------------------------------------------------------------
class CharactersState(BaseState):
    """State for selecting and saving characters."""

    SELECTION_COLOR = (255, 0, 128)  # Pink color for selection mode
    
    def __init__(self, controller):
        super().__init__(controller)
        self.selected_index = controller.selected_character
        self.preview_character = Character(CHARACTERS_DATA[self.selected_index])
    
    def on_enter(self):
        print(f"Entering CharactersState - Showing: {CHARACTERS_DATA[self.selected_index]['name']}")
    
    def update(self, current_time):
        pass
    
    def handle_short_press(self):
        # Cycle through characters
        self.selected_index = (self.selected_index + 1) % len(CHARACTERS_DATA)
        
        # Create new character and force animation to start from beginning of interval
        new_character = Character(CHARACTERS_DATA[self.selected_index])
        current_time = time.ticks_ms()
        
        # Force animations to start from the beginning of their interval
        for anim in new_character.animations.values():
            anim['last_trigger'] = current_time  # Set to current time
        
        self.preview_character = new_character
        print(f"Selected character: {CHARACTERS_DATA[self.selected_index]['name']}")
    
    def handle_long_press(self):
        # Save selection and return to DefaultState
        self.controller.selected_character = self.selected_index
        success = self.controller.save_character(self.selected_index)
        if success:
            print(f"Saved character selection: {CHARACTERS_DATA[self.selected_index]['name']}")
        else:
            print("Warning: Failed to save character selection")
        self.controller.switch_to(DefaultState(self.controller))
    
    def update_display(self):
        # Render the character with the selection color
        self.preview_character.render(
            mode="available",  # Use available mode as base
            np=self.controller.np,
            brightness=BRIGHTNESS,
            selection_color=self.SELECTION_COLOR
        )

# --------------------------------------------------------------------------------
# PomodoroState
# --------------------------------------------------------------------------------
class PomodoroState(BaseState):
    """State for Pomodoro timers with sub-states: INTRO, SETUP, ACTIVE, COMPLETE."""
    
    COLORS = {
        "intro": (255, 128, 0),    # Light orange
        "setup": (255, 165, 0),    # Orange
        "active": (255, 69, 0),    # Red-orange
        "complete": (255, 215, 0), # Gold
    }
    
    def __init__(self, controller):
        super().__init__(controller)
        self.sub_state = "intro"
        self.intro_start_time = time.ticks_ms()
        self.pomodoro_setup_start = None
        self.pomodoro_start_time = None
        self.pomodoro_duration = 15  # Start with 15 minutes
    
    def on_enter(self):
        print("Entering PomodoroState / INTRO")
        self.sub_state = "intro"
        self.intro_start_time = time.ticks_ms()
    
    def update(self, current_time):
        # Transition from INTRO to SETUP
        if self.sub_state == "intro":
            if time.ticks_diff(current_time, self.intro_start_time) >= INTRO_DURATION:
                self.sub_state = "setup"
                self.pomodoro_setup_start = current_time
                print("Auto: Pomodoro INTRO → SETUP")
        
        # Transition from SETUP to ACTIVE if time runs out
        elif self.sub_state == "setup":
            if time.ticks_diff(current_time, self.pomodoro_setup_start) >= POMODORO_SETUP_TIMEOUT:
                self.sub_state = "active"
                self.pomodoro_start_time = current_time
                print("Auto: Pomodoro SETUP → ACTIVE (timeout)")
    
    def handle_short_press(self):
        # Adjust or switch sub-states
        if self.sub_state == "setup":
            # Increase pomodoro duration in increments of 15, up to 60
            self.pomodoro_duration += 15
            if self.pomodoro_duration > 60:
                self.pomodoro_duration = 15
            # Reset the setup timeout start
            self.pomodoro_setup_start = time.ticks_ms()
            print(f"Short press: Pomodoro duration: {self.pomodoro_duration} minutes")
        
        elif self.sub_state == "active":
            # Interrupt pomodoro
            self.sub_state = "complete"
            print("Short press: Pomodoro ACTIVE → COMPLETE (interrupted)")
        
        elif self.sub_state == "complete":
            # Restart pomodoro from intro
            self.sub_state = "intro"
            self.intro_start_time = time.ticks_ms()
            print("Short press: Pomodoro COMPLETE → INTRO (restart)")
    
    def handle_long_press(self):
        # Long press: go back to DefaultState (intro)
        print("Long press: Pomodoro → Default INTRO")
        self.controller.switch_to(DefaultState(self.controller))
    
    def update_display(self):
        color = self.COLORS.get(self.sub_state, (255, 255, 255))
        self._fill_solid_color(color)

# --------------------------------------------------------------------------------
# UpdateState
# --------------------------------------------------------------------------------
class UpdateSubState:
    """Update process states"""
    CONNECTING = "connecting"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    ERROR = "error"

class UpdateState(BaseState):
    """Handles WiFi connection and update process."""

    COLORS = {
        'CONNECTING': (0, 0, 255),    # Blue
        'CHECKING': (128, 0, 255),    # Purple
        'DOWNLOADING': (80, 0, 0),    # Red
        'INSTALLING': (255, 128, 0),  # Orange
        'ERROR': (255, 0, 0),         # Red
    }

    # Define spinner properties
    BACKGROUND_BRIGHTNESS = 0.1  # Background at 10% brightness
    SPINNER_BRIGHTNESS = 0.4  # Spinner will be 40% brighter than background
    SPINNER_SPEED = 100  # ms per step
    
    def __init__(self, controller):
        super().__init__(controller)
        self.error = None
        self.spinner_position = 0
        self.last_spinner_update = time.ticks_ms()
    
    def _update_spinner(self, base_color):
        """Update spinner animation."""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_spinner_update) >= self.SPINNER_SPEED:
            self.spinner_position = (self.spinner_position + 1) % 28
            self.last_spinner_update = current_time
        
        # Create dimmer background color
        background_color = tuple(int(c * self.BACKGROUND_BRIGHTNESS) for c in base_color)
        
        # Create brighter spinner color
        spinner_color = tuple(int(c * self.SPINNER_BRIGHTNESS) for c in base_color)
        
        # Fill with dim background
        self.controller.np.fill(background_color)
        
        # Draw spinner with trail
        border_pixels = self._get_border_pixels()
        for i in range(5):  # 5 pixel trail
            pos = (self.spinner_position - i) % len(border_pixels)
            row, col = border_pixels[pos]
            brightness = (5 - i) / 5  # Fade trail from 100% to 0%
            
            # Calculate color for this trail pixel
            color = tuple(
                int(background_color[j] + (spinner_color[j] - background_color[j]) * brightness)
                for j in range(3)
            )
            self.controller.np[self._get_pixel_index(row, col)] = color
        
        self.controller.np.write()
        
    def on_enter(self, **kwargs):
        super().on_enter(**kwargs)
        self.sub_state = UpdateSubState.CONNECTING
        print("Starting update check...")
        self._fill_solid_color(self.COLORS['CONNECTING'])
        
    def update(self, current_time):
        # Handle spinner states
        if self.sub_state in [UpdateSubState.CONNECTING, UpdateSubState.CHECKING, UpdateSubState.INSTALLING]:
            self._update_spinner(self.COLORS[self.sub_state.upper()])
        # Handle error state with solid color
        elif self.sub_state == UpdateSubState.ERROR:
            self._fill_solid_color(self.COLORS[self.sub_state.upper()])
        # Download state is handled by progress bar in _handle_download
        
        # Regular state handling
        if self.sub_state == UpdateSubState.CONNECTING:
            self._handle_wifi_connection()
        elif self.sub_state == UpdateSubState.CHECKING:
            self._handle_version_check()
        elif self.sub_state == UpdateSubState.DOWNLOADING:
            self._handle_download()
        elif self.sub_state == UpdateSubState.INSTALLING:
            self._handle_install()

    def _handle_wifi_connection(self):
        """Handle WiFi connection attempt with animation."""
        try:
            # Only try to connect if we haven't started yet
            if not hasattr(self, '_wifi_connection_started'):
                self._wifi_connection_started = True
                self._connection_start_time = time.ticks_ms()
                
                # Use shared WiFi connection start
                success, message = WiFiManager.start_connection()
                if not success:
                    raise Exception(message)
            
            # Check connection status using shared function
            if WiFiManager.check_connection():
                print("WiFi connected!")
                delattr(self, '_wifi_connection_started')
                self.sub_state = UpdateSubState.CHECKING
            elif time.ticks_diff(time.ticks_ms(), self._connection_start_time) > WIFI_TIMEOUT_SECONDS * 1000:
                raise Exception("WiFi connection timeout")

        except Exception as e:
            self._handle_error("WiFi connection failed", e)

    def _handle_version_check(self):
        """Check for available updates."""
        try:
            # Only start version check if we haven't yet
            if not hasattr(self, '_version_check_started'):
                self._version_check_started = True
                self._version_check_start_time = time.ticks_ms()
                
                # Do the actual version check
                content = self._fetch_github_raw()
                if not content:
                    raise Exception("Failed to fetch version info")
                    
                self._update_info = json.loads(content)
                print(f"Current version: {CURRENT_VERSION}")
                print(f"Latest version: {self._update_info['version']}")
            
            # Check if enough time has passed (2 seconds)
            if time.ticks_diff(time.ticks_ms(), self._version_check_start_time) >= 2000:
                # Time has passed, proceed with state change
                delattr(self, '_version_check_started')  # Reset for next time
                
                if self._update_info['version'] > CURRENT_VERSION or FORCE_UPDATE:
                    if FORCE_UPDATE:
                        print("Force update enabled - downloading firmware...")
                    else:
                        print(f"Update available: {self._update_info['version']}")
                        
                    # Store the URL before changing state
                    self.controller.transition_data['update_url'] = self._update_info['url']
                    self.sub_state = UpdateSubState.DOWNLOADING
                else:
                    print("No update needed")
                    machine.reset()
                    
        except Exception as e:
            self._handle_error("Version check failed", e)
        
    def _fetch_github_raw(self):
        try:
            response = urequests.get(UPDATE_URL)
            content = None
            if response.status_code == 200:
                content = response.text  # Store before closing
            response.close()  # Always close even on error
            return content.strip() if content else None
        except Exception as e:
            print(f"GitHub fetch failed: {e}")
            return None
            
    def _fill_progress_bar(self, color, progress):
        """
        Fill display with a progress bar.
        progress should be 0.0 to 1.0
        """
        # Create dimmed background color
        background_color = tuple(int(c * self.BACKGROUND_BRIGHTNESS) for c in color)
        
        # Fill background
        self.controller.np.fill(background_color)
        
        # Calculate how many columns to fill (out of 8)
        filled_cols = min(8, int(progress * 8))
        
        # Fill the progress bar
        for row in range(8):
            for col in range(filled_cols):
                self.controller.np[self._get_pixel_index(row, col)] = color
                
        self.controller.np.write()

    def _handle_download(self):
        """Download new firmware with progress bar."""
        try:
            url = self.controller.transition_data.get('update_url')
            if not url:
                raise Exception("No update URL")

            print("Starting download...")
    
            # Get content length first
            response = urequests.get(url, stream=True)
            if response.status_code != 200:
                raise Exception(f"Download failed: {response.status_code}")

            total_size = int(response.headers.get('Content-Length', 0))
            bytes_downloaded = 0

            
            # Open file for immediate writing
            with open('main.py.new', 'wb') as f:
                # Use much smaller chunks (16 bytes)
                chunk_size = 16

                 # Progress tracking optimization
                progress_interval = 512  # Only update UI every 512 bytes
                last_progress_update = 0

                while True:
                    chunk = response.raw.read(chunk_size)
                    if not chunk:
                        break

                    # Write each chunk immediately
                    f.write(chunk)
                    bytes_downloaded += len(chunk)

                    # Update progress bar LESS frequently (not every 256 bytes)
                    if bytes_downloaded - last_progress_update >= progress_interval:
                        progress = bytes_downloaded / total_size
                        self._fill_progress_bar(self.COLORS['DOWNLOADING'], progress)
                        last_progress_update = bytes_downloaded

                        # Print memory every 5KB
                        if bytes_downloaded % 5120 == 0:
                            print("Downloaded:", bytes_downloaded, "/", total_size, "bytes")
                        
                        # Force garbage collection after UI updates
                        gc.collect()

            response.close()
            
            # Show complete state briefly
            self._fill_progress_bar(self.COLORS['DOWNLOADING'], 1.0)
            time.sleep(0.3)
            
            self.sub_state = UpdateSubState.INSTALLING
            
        except Exception as e:
            self._handle_error("Download failed", e)
            
    def _handle_install(self):
        """Install new firmware and reset."""
        try:
            # Only start install if we haven't yet
            if not hasattr(self, '_install_started'):
                self._install_started = True
                self._install_start_time = time.ticks_ms()
                
                try:
                    os.remove('main.py.bak')
                except:
                    pass 
                    
                os.rename('main.py', 'main.py.bak')
                os.rename('main.py.new', 'main.py')
                print("Files renamed, waiting before reboot...")

                # Ensure WiFi is disconnected before reboot
                WiFiManager.disconnect()
            
            # Wait for 2 seconds while showing spinner
            if time.ticks_diff(time.ticks_ms(), self._install_start_time) >= 2000:
                print("Installation complete, rebooting...")
                machine.reset()
                
        except Exception as e:
            self._handle_error("Installation failed", e)
    
    def _handle_error(self, message, error):
        """Centralized error handling with flashing animation."""
        print(f"{message}: {error}")
        self.error = str(error)
        self.sub_state = UpdateSubState.ERROR
        
        # Flash red 3 times
        for _ in range(3):
            self._fill_solid_color((0, 0, 0))
            time.sleep(0.2)
            self._fill_solid_color(self.COLORS['ERROR'])
            time.sleep(0.2)
        
        # Brief pause before reboot
        time.sleep(0.5)
        machine.reset()

# --------------------------------------------------------------------------------
# Time Management
# --------------------------------------------------------------------------------
class TimeManager:
    """Manages time synchronization with NTP servers with timezone support."""
    
    def __init__(self):
        self.rtc = machine.RTC()
        self.is_synced = False
        self.timezone_offset = 1  # Sweden is UTC+1 by default (CET)
    
    def sync_time(self):
        """Synchronize RTC with network time and adjust for timezone."""
        try:
            # Start connection
            success, message = WiFiManager.start_connection()
            if not success:
                print(f"WiFi connection failed: {message}")
                return False
                
            # Wait for connection with timeout
            start_time = time.ticks_ms()
            while not WiFiManager.check_connection():
                if time.ticks_diff(time.ticks_ms(), start_time) > WIFI_TIMEOUT_SECONDS * 1000:
                    print("WiFi connection timeout")
                    return False
                time.sleep(0.1)
                
            # Proceed with time sync to get UTC time
            ntptime.settime()
            
            # Get and adjust for timezone
            datetime = self.rtc.datetime()
            y, mo, d, wd, h, mi, s, ms = datetime
            
            # Apply timezone offset (with simplified DST calculation)
            offset_hours = self.timezone_offset
            if self._is_dst_simplified(mo, d):
                offset_hours += 1
            
            h = (h + offset_hours) % 24
            
            # Update RTC with adjusted time
            self.rtc.datetime((y, mo, d, wd, h, mi, s, ms))
            self.is_synced = True
            
            # Get and display current time
            print(f"Time synced: {y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}")
            print(f"Timezone: UTC+{offset_hours} ({'CEST' if offset_hours > 1 else 'CET'})")
            return True
            
        except Exception as e:
            print(f"Time sync failed: {e}")
            return False
        finally:
            WiFiManager.disconnect()
    
    def _is_dst_simplified(self, month, day):
        """
        Simplified DST calculation for EU:
        - Last Sunday of March (approx. March 25-31) to 
        - Last Sunday of October (approx. October 25-31)
        
        This is not 100% accurate for edge cases, but works well enough
        for most practical purposes.
        """
        if month < 3 or month > 10:  # Jan, Feb, Nov, Dec
            return False
        if month > 3 and month < 10:  # Apr to Sep
            return True
        if month == 3 and day >= 25:  # Late March (approximate)
            return True
        if month == 10 and day < 25:  # Early October (approximate)
            return True
        return False
    
    def is_time_set(self):
        """Check if the time has been set reasonably."""
        y, _, _, _, _, _, _, _ = self.rtc.datetime()
        # If year is before 2023, the time is probably not set
        return y >= 2023 and self.is_synced
    
    def get_datetime(self):
        """Get current datetime as a tuple (y, mo, d, h, mi, s)."""
        dt = self.rtc.datetime()
        return dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]  # Year, month, day, hour, minute, second

    def is_midnight(self):
        """Check if it's update time (03:00-03:30)."""
        dt = self.rtc.datetime()
        _, _, _, _, h, m, _, _ = dt

        # Debug override: Uncomment to force test time interval between 17:00 and 17:10
        # return h == 17 and m < 10

        # If after 3 AM and before 3:30 AM
        return h == 3 and m < 45
    
    def is_friyay_time(self):
        """Check if it's FRIYAY time (Friday 15:00 to Saturday 02:00)."""

        # Check if time is set, otherwise weekdays can be wrong.
        if not self.is_time_set():
            return False
            
        dt = self.rtc.datetime()
        _, _, _, weekday, hour, minute, _, _ = dt

        # Debug override: Uncomment to force test time interval between 17:00 and 17:10
        # return hour == 19 and minute < 6
         
        # If after Friday (4) 15:00 and before Saturday (5) 02:00 AM
        return (weekday == 4 and hour >= 15) or (weekday == 5 and hour < 2)
    
# --------------------------------------------------------------------------------
# StateController - Manages switching and delegates logic
# --------------------------------------------------------------------------------
class StateController:
    """Enhanced state controller with transition management."""
    def __init__(self, np):
        self.np = np

        # Clear display on initialization
        self.np.fill((0, 0, 0))
        self.np.write()

        self.current_state = None
        self.transition_data = {}  # For passing data between states
        self.selected_character = self._load_saved_character()  # Load saved character
        self.time_manager = TimeManager()  # Add time manager
        self.last_day_checked = None  # For tracking latest updated day
        self.last_friyay_check = time.ticks_ms()  # Add this line
    
    def _load_saved_character(self):
        """Load the saved character ID from storage."""
        try:
            with open("char_config.json", "r") as f:
                saved_id = json.load(f)
                # Find the index of the character with this ID
                for idx, char_data in enumerate(CHARACTERS_DATA):
                    if char_data['id'] == saved_id:
                        return idx
        except:
            pass  # Any error, return default
        return 0  # Default to first character

    def save_character(self, index):
        """Save the selected character ID to storage."""
        try:
            char_id = CHARACTERS_DATA[index]['id']
            with open("char_config.json", "w") as f:
                json.dump(char_id, f)
            return True
        except Exception as e:
            print(f"Failed to save character config: {e}")
            return False
    
    def switch_to(self, new_state, **kwargs):
        """
        Enhanced state transition with data passing.
        
        Args:
            new_state: The new state to switch to
            **kwargs: Optional data to pass to the new state
        """
        if self.current_state:
            self.current_state.on_exit()
            
        self.current_state = new_state
        self.current_state.on_enter(**kwargs)
    
    def update(self, current_time):
        if self.current_state:
            self.current_state.update(current_time)
    
    def handle_short_press(self):
        if self.current_state:
            self.current_state.handle_short_press()
    
    def handle_long_press(self):
        if self.current_state:
            self.current_state.handle_long_press()
    
    def update_display(self):
        if self.current_state:
            self.current_state.update_display()

    def check_scheduled_updates(self):
        """Check if it's time for a scheduled update."""
        print("Checking for scheduled updates...")

        if not self.time_manager.is_time_set():
            print("Time not set, skipping scheduled update check")
            return  # Can't check if time isn't set
        
        # Get current date
        current_date = self.time_manager.get_datetime()[:3]

        # Only proceed if:
        # 1. It's update time (3:00-3:30)
        # 2. We haven't updated today
        if (self.time_manager.is_midnight() and 
            current_date != self.last_day_checked):
            
            print("🔄 Update time detected - initiating scheduled update")
            self.last_day_checked = current_date
            self.switch_to(UpdateState(self))

    def check_scheduled_friyay(self):
        """Check if it's time for FRIYAY mode."""
        print("Checking for friyay...")
        if not self.time_manager.is_time_set():
            return  # Can't check if time isn't set
        
        # Skip if we're not in default state
        if not isinstance(self.current_state, DefaultState):
            return
                
        # Get current default state
        default_state = self.current_state
        
        # Skip intro animation
        if default_state.sub_state == DefaultSubState.INTRO:
            return
        
        # Check if it's FRIYAY time
        is_friyay_time = self.time_manager.is_friyay_time()
        
        # Update cycle states based on whether it's Friyay time
        if is_friyay_time:
            # Add FRIYAY to cycle if it's not there
            if DefaultSubState.FRIYAY not in DefaultSubState.CYCLE_STATES:
                DefaultSubState.CYCLE_STATES = DefaultSubState.BASE_CYCLE_STATES + [DefaultSubState.FRIYAY]
                print("FRIYAY mode added to cycle!")
                
                # Only auto-switch to FRIYAY if we're not in BUSY and not already in FRIYAY
                if (default_state.sub_state != DefaultSubState.BUSY and 
                    default_state.sub_state != DefaultSubState.FRIYAY):
                    print("It's FRIYAY time! Switching to FRIYAY mode")
                    default_state.sub_state = DefaultSubState.FRIYAY
        else:
            # Remove FRIYAY from cycle if it's there
            if DefaultSubState.FRIYAY in DefaultSubState.CYCLE_STATES:
                DefaultSubState.CYCLE_STATES = DefaultSubState.BASE_CYCLE_STATES.copy()
                print("FRIYAY mode removed from cycle!")
                
                # If we're in FRIYAY mode, switch to AVAILABLE
                if default_state.sub_state == DefaultSubState.FRIYAY:
                    default_state.sub_state = DefaultSubState.AVAILABLE
                    print("Switching from FRIYAY to AVAILABLE (no longer Friyay time)")


# --------------------------------------------------------------------------------
# Main Loop
# --------------------------------------------------------------------------------
def main():
    # Initialize hardware
    np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

    # IMMEDIATE CLEAR - turn off all LEDs as the very first action
    np.fill((0, 0, 0))
    np.write()

    button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    controller = StateController(np)

    # Initialize state variables
    button_state = {
        'pressed': False,
        'press_start': 0,
        'long_press_handled': False
    }
    
    background_state = {
        'intro_complete': False,
        'wifi_started': False,
        'time_synced': False,
        'wifi_start_time': None,
        'last_schedule_check': time.ticks_ms(),
        'last_friyay_check': time.ticks_ms()
    }

    # Handle boot sequence
    if button.value() == 0:  # Boot with button held
        controller.switch_to(CharactersState(controller))
        controller.update_display()
        print("Entering CHARACTERS mode (boot override)")
        
        boot_start = time.ticks_ms()
        while button.value() == 0:
            if time.ticks_diff(time.ticks_ms(), boot_start) >= UPDATE_CHECK_TIME:
                controller.switch_to(UpdateState(controller))
                break
    else:  # Normal boot
        controller.switch_to(DefaultState(controller))
        print("Starting in DEFAULT mode")

    # Main loop
    while True:
        current_time = time.ticks_ms()
        
        # Handle background tasks
        if isinstance(controller.current_state, DefaultState):
            # Track intro completion
            if not background_state['intro_complete']:
                if controller.current_state.sub_state != DefaultSubState.INTRO:
                    background_state['intro_complete'] = True
                    background_state['wifi_start_time'] = current_time
            
            # Handle WiFi and time sync
            elif not background_state['time_synced']:
                if not background_state['wifi_started']:
                    success, message = WiFiManager.start_connection()
                    background_state['wifi_started'] = True
                    if not success:
                        print(f"Background WiFi connection failed: {message}")
                        background_state['time_synced'] = True
                
                elif WiFiManager.check_connection():
                    if controller.time_manager.sync_time():
                        print("Background time sync successful")
                    else:
                        print("Background time sync failed")
                    background_state['time_synced'] = True
                    WiFiManager.disconnect()
                
                elif time.ticks_diff(current_time, background_state['wifi_start_time']) > WIFI_TIMEOUT_SECONDS * 1000:
                    print("Background WiFi connection timed out")
                    background_state['time_synced'] = True

        # Update state and check schedules
        controller.update(current_time)
        if time.ticks_diff(current_time, background_state['last_schedule_check']) >= SCHEDULED_UPDATE_CHECK:
            controller.check_scheduled_updates()
            background_state['last_schedule_check'] = current_time

        # Check if it's FRIYAY time
        if time.ticks_diff(current_time, background_state['last_friyay_check']) >= SCHEDULED_FRIYAY_CHECK:
            controller.check_scheduled_friyay()
            background_state['last_friyay_check'] = current_time

        # Handle button input
        if isinstance(controller.current_state, DefaultState) and controller.current_state.sub_state == DefaultSubState.INTRO:
            # Ignore button during intro, but reset state on release
            if button.value() == 1:
                button_state['pressed'] = False
                button_state['long_press_handled'] = False
        else:
            # Normal button handling
            if button.value() == 0:  # Pressed
                if not button_state['pressed']:
                    button_state['pressed'] = True
                    button_state['press_start'] = current_time
                else:
                    press_duration = time.ticks_diff(current_time, button_state['press_start'])
                    if press_duration >= LONG_PRESS_TIME and not button_state['long_press_handled']:
                        controller.handle_long_press()
                        button_state['long_press_handled'] = True
            else:  # Released
                if button_state['pressed']:
                    press_duration = time.ticks_diff(current_time, button_state['press_start'])
                    if press_duration < LONG_PRESS_TIME:
                        controller.handle_short_press()
                    button_state['pressed'] = False
                    button_state['long_press_handled'] = False

        # Update display
        controller.update_display()
        time.sleep(0.01)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")