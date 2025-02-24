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
import random

# --------------------------------------------------------------------------------
# Hardware Configuration
# --------------------------------------------------------------------------------
LED_PIN = 0
BUTTON_PIN = 10
NUM_LEDS = 64
BRIGHTNESS = 0.1

# --------------------------------------------------------------------------------
# Timing Configuration
# --------------------------------------------------------------------------------
LONG_PRESS_TIME = 700       # 0.7 seconds for long press
UPDATE_CHECK_TIME = 4000    # 8 seconds for update check
INTRO_DURATION = 1000       # 1 second for intro animations
POMODORO_SETUP_TIMEOUT = 5000  # 5 seconds before auto-starting
INTRO_DURATION = 5000       # 5 seconds for intro animations

# GitHub OTA Update Configuration
FORCE_UPDATE = True  # Set this to True to force update regardless of version
WIFI_TIMEOUT_SECONDS = 5    # Seconds to wait before timeout
WIFI_CONNECT_ATTEMPTS = 2   # Initial attempt + 2 retries
CURRENT_VERSION = "1.0.4"
GITHUB_USER = "underverket"
GITHUB_REPO = "dnd"
UPDATE_URL = f"http://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/firmware.json"

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
class CharacterDefinition:
    """Convert ASCII art style definitions into pixel data"""
    @staticmethod
    def process_layer(ascii_art):
        pixels = []
        for row, line in enumerate(ascii_art):
            for col, char in enumerate(line.split()):
                if char == 'X':
                    pixels.append((row, col))
        return pixels

    @staticmethod
    def create_character(data):
        """Convert a character definition into processed pixel data"""
        character = {
            'id': data['id'],
            'name': data['name'],
            'pixels': []
        }
        
        # Process standard layers if they exist
        if 'body' in data:
            body_pixels = CharacterDefinition.process_layer(data['body'])
            for pixel in body_pixels:
                character['pixels'].append({
                    'row': pixel[0],
                    'col': pixel[1],
                    'type': 'body'
                })
                
        if 'hl' in data:
            highlight_pixels = CharacterDefinition.process_layer(data['hl'])
            for pixel in highlight_pixels:
                character['pixels'].append({
                    'row': pixel[0],
                    'col': pixel[1],
                    'type': 'highlight'
                })
                
        if 'sdw' in data:
            shadow_pixels = CharacterDefinition.process_layer(data['sdw'])
            for pixel in shadow_pixels:
                character['pixels'].append({
                    'row': pixel[0],
                    'col': pixel[1],
                    'type': 'shadow'
                })
        
        # Handle custom colored pixels if they exist
        if 'custom' in data:
            for pixel in data['custom']:
                character['pixels'].append({
                    'row': pixel['row'],
                    'col': pixel['col'],
                    'type': 'fixed',
                    'color': pixel['color']
                })
        
        # Add animations if they exist
        if 'animations' in data:
            character['animations'] = data['animations']
                
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
                    'frames': [CharacterDefinition.process_layer(frame) for frame in anim['frames']],
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
CHARACTERS_RAW = [
    {
        "id": "ghost_plain",
        "name": "Plain Ghost",
        "body": [
            "_ _ X X X X _ _",
            "_ X X X X X X _",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X _ X _ X _ X _"
        ],
        "animations": [
            {
                "name": "blink",
                "interval": 3000,
                "frame_duration": 50,
                "reverse": False,
                "color": (255, 255, 255),
                "frames": [
                    [   # Frame 1 - Eyes open
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2 - Eyes half closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 3 - Eyes closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ]
                ]
            }
        ]
    },
    {
        "id": "ghost_fancy",
        "name": "Fancy Ghost",
        "body": [
            "_ _ X X X X _ _",
            "_ X X X X X X _",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X _ X _ X _ X _"
        ],
        # Eyes
        "custom": [
            {'row': 4, 'col': 2, 'color': (255, 0, 0)},    # Red
            {'row': 4, 'col': 5, 'color': (255, 0, 0)},    # Red
            {'row': 5, 'col': 2, 'color': (255, 127, 0)},  # Orange
            {'row': 5, 'col': 5, 'color': (255, 127, 0)},  # Orange
        ],
        "hl": [
            "_ _ _ _ _ X _ _",
            "_ _ _ _ _ _ X _",
            "_ _ _ _ _ _ _ X",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _"
        ],
        "sdw": [
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "X _ _ _ _ _ _ _",
            "X _ _ _ _ _ _ _",
            "X _ _ _ _ _ _ _",
            "X _ _ _ _ _ _ _",
            "X X _ _ _ _ _ _",
            "X _ X _ _ _ _ _"
        ]
    },
    {
        "id": "ghost_colorful",
        "name": "Colorful Ghost",
        "body": [
            "_ _ X X X X _ _",
            "_ X X X X X X _",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X _ X _ X _ X _"
        ],
        "custom": [
            # Hat
            {'row': 0, 'col': 2, 'color': (255, 0, 0)},    # Red
            {'row': 0, 'col': 3, 'color': (255, 127, 0)},  # Orange
            {'row': 0, 'col': 4, 'color': (255, 255, 0)},  # Yellow
            {'row': 0, 'col': 5, 'color': (0, 255, 0)},    # Green
            # Eyes
            {'row': 4, 'col': 2, 'color': (255, 0, 0)},    # Red
            {'row': 4, 'col': 5, 'color': (255, 0, 0)},    # Red
            {'row': 5, 'col': 2, 'color': (255, 127, 0)},  # Orange
            {'row': 5, 'col': 5, 'color': (255, 127, 0)},  # Orange
        ]
    }
]

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
    
    # States that we cycle through with short press
    CYCLE_STATES = [AVAILABLE, BUSY, SOCIAL]

class DefaultState(BaseState):
    """Main 'Default' state with sub-states: INTRO, AVAILABLE, BUSY, SOCIAL."""

    ANIMATION_DURATION = 600  # Total duration in milliseconds
    
    def __init__(self, controller):
        super().__init__(controller)
        self.sub_state = DefaultSubState.INTRO
        self.character = Character(CHARACTERS_DATA[controller.selected_character])
        self.animation_start = None
    
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
            current_idx = DefaultSubState.CYCLE_STATES.index(self.sub_state)
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
        else:
            # Normal rendering
            self.character.render(
                mode=self.sub_state,
                np=self.controller.np,
                brightness=BRIGHTNESS
            )

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
        'DOWNLOADING': (255, 0, 0),   # Red
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
        """Handle WiFi connection attempt."""
        try:
            # Only try to connect if we haven't started yet
            if not hasattr(self, '_wifi_connection_started'):
                self._wifi_connection_started = True
                try:
                    from wifi_config import WIFI_SSID, WIFI_PASSWORD
                    print(f"🔍 Loaded Wi-Fi config - SSID: {WIFI_SSID}")
                except ImportError:
                    raise Exception("No WiFi credentials file")
                    
                if not WIFI_SSID or not WIFI_PASSWORD:
                    raise Exception("No WiFi credentials")
                    
                wlan = network.WLAN(network.STA_IF)
                wlan.active(True)
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                self._connection_start_time = time.ticks_ms()
            
            # Check connection status
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                print("WiFi connected!")
                delattr(self, '_wifi_connection_started')  # Reset for next time
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
        """Fetch version info from GitHub."""
        try:
            response = urequests.get(UPDATE_URL)
            if response.status_code == 200:
                content = response.text
                response.close()
                return content.strip()
            response.close()
            return None
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

            # Get content length first
            response = urequests.get(url, stream=True)
            if response.status_code != 200:
                raise Exception(f"Download failed: {response.status_code}")

            total_size = int(response.headers.get('Content-Length', 0))
            bytes_downloaded = 0
            all_content = []

            while True:
                chunk = response.raw.read(64)  # Read in smaller chunks
                if not chunk:
                    break

                bytes_downloaded += len(chunk)
                all_content.append(chunk)
                
                # Update progress bar
                progress = bytes_downloaded / total_size
                self._fill_progress_bar(self.COLORS['DOWNLOADING'], progress)

            response.close()
            
            # Write the complete file
            content = b''.join(all_content).decode()
            with open('main.py.new', 'w') as f:
                f.write(content)

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
# StateController - Manages switching and delegates logic
# --------------------------------------------------------------------------------
class StateController:
    """Enhanced state controller with transition management."""
    def __init__(self, np):
        self.np = np
        self.current_state = None
        self.transition_data = {}  # For passing data between states
        self.selected_character = self._load_saved_character()  # Load saved character
    
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

# --------------------------------------------------------------------------------
# Main Loop
# --------------------------------------------------------------------------------
def main():
    # Initialize hardware
    np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)
    button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    controller = StateController(np)
    
    # Boot sequence: check if button is held to jump to CharactersState or UpdateState
    boot_start = time.ticks_ms()
    if button.value() == 0:  # If button is held during boot
        # Immediately go to CharactersState
        # controller.switch_to(CharactersState(controller))
        # controller.update_display()
        
        # print("Entering CHARACTERS mode (boot override)")
        controller.switch_to(CharactersState(controller))
        controller.update_display()
        print("Entering CHARACTERS mode (boot override)")
        
        # Then wait to see if it becomes an update check
        while button.value() == 0:  # While button is still held
            if time.ticks_diff(time.ticks_ms(), boot_start) >= UPDATE_CHECK_TIME:
                # Switch to UpdateState
                controller.switch_to(UpdateState(controller))
                # The UpdateState immediately resets the board in on_enter()
                # If we somehow didn't reset, break anyway
                break

    else:
        # Default startup - add this line
        controller.switch_to(DefaultState(controller))
        print("Starting in DEFAULT mode")
    
    # Button handling variables
    button_pressed = False
    press_start_time = 0
    long_press_handled = False
    
    # Main loop
    while True:
        current_time = time.ticks_ms()
        
        # Update the current state (for time-based transitions)
        controller.update(current_time)
        
        # Check button status
        if button.value() == 0:  # Button is pressed
            if not button_pressed:
                button_pressed = True
                press_start_time = current_time
            else:
                # Check for long press
                press_duration = time.ticks_diff(current_time, press_start_time)
                if press_duration >= LONG_PRESS_TIME and not long_press_handled:
                    controller.handle_long_press()
                    long_press_handled = True
        else:  # Button is released
            if button_pressed:
                press_duration = time.ticks_diff(current_time, press_start_time)
                if press_duration < LONG_PRESS_TIME:
                    controller.handle_short_press()
                long_press_handled = False
                button_pressed = False
        
        # Update LED display
        controller.update_display()
        
        # Small delay to prevent busy waiting
        time.sleep(0.01)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")