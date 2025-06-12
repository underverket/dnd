#!/usr/bin/env python3
"""
Character Pattern Compression Tool

This script:
1. Reads character definitions from chars.py
2. Compresses patterns into hex format
3. Outputs compressed definitions for copy-pasting
"""

# --------------------------------------------------------------------------------
# Character Encoding System
# --------------------------------------------------------------------------------
# Characters are stored in a compressed hex format where:
# - Each 8x8 pattern is represented by 16 hex characters (8 bytes)
# - Each byte (2 hex chars) represents one row
# - Within each byte, each bit represents a pixel (1=on, 0=off)
# 
# For example, "3C7EFFFFFFFFFF55" decodes to:
# "_ _ X X X X _ _"  # 3C = 00111100
# "_ X X X X X X _"  # 7E = 01111110
# "X X X X X X X X"  # FF = 11111111
# "X X X X X X X X"  # FF = 11111111
# "X X X X X X X X"  # FF = 11111111
# "X X X X X X X X"  # FF = 11111111
# "X X X X X X X X"  # FF = 11111111
# "X _ X _ X _ X _"  # 55 = 01010101
#
# Characters are built from these patterns with different "types":
# - body: The main character outline
# - hl: Highlights (brighter areas)
# - sdw: Shadows (darker areas)
# - custom: Fixed-color pixels
# --------------------------------------------------------------------------------

import os
import sys
import pprint

def pattern_to_hex(pattern):
    """Convert a text pattern (8x8) to hex representation"""
    hex_result = ""
    for row in pattern:
        # Remove spaces and convert to binary (X=1, _=0)
        binary = ''.join('1' if char == 'X' else '0' for char in row if char in 'X_')
        # Convert binary to hex
        hex_byte = f"{int(binary, 2):02X}"
        hex_result += hex_byte
    return hex_result

def compress_frames(frames):
    """Compress animation frames to hex patterns"""
    return [pattern_to_hex(frame) for frame in frames]

def custom_format(obj, indent=0):
    """Custom formatter that keeps certain arrays on a single line"""
    spaces = ' ' * indent
    
    if isinstance(obj, list):
        # Check if it's a list of simple values or a specific case
        is_simple = all(not isinstance(x, (dict, list)) for x in obj)
        
        if len(obj) == 0:
            return "[]"
        elif is_simple:
            # Simple list - format on a single line
            items = [repr(item) for item in obj]
            return "[" + ", ".join(items) + "]"
        else:
            # Complex list - format each item on a new line
            items = [custom_format(item, indent + 4) for item in obj]
            result = "[\n"
            for i, item_str in enumerate(items):
                result += spaces + "    " + item_str
                if i < len(items) - 1:
                    result += ","
                result += "\n"
            result += spaces + "]"
            return result
            
    elif isinstance(obj, dict):
        if len(obj) == 0:
            return "{}"
            
        result = "{\n"
        
        # Process keys in a specific order for consistency
        keys = sorted(obj.keys())
        
        for i, key in enumerate(keys):
            value = obj[key]
            
            # Special handling for animations and custom arrays
            if key in ["animations", "custom"]:
                # Format these fields to keep inner arrays on a single line
                if isinstance(value, list):
                    if key == "animations":
                        # For animations, keep the inner list compact
                        inner_items = []
                        for anim in value:
                            if isinstance(anim, list):
                                # Process animation list
                                anim_items = [repr(item) if not isinstance(item, list) else "[" + ", ".join(repr(i) for i in item) + "]" for item in anim]
                                inner_items.append("[" + ", ".join(anim_items) + "]")
                            else:
                                inner_items.append(repr(anim))
                        value_str = "[" + ", ".join(inner_items) + "]"
                    else:
                        # For custom pixels, keep the list compact
                        inner_items = [repr(item) for item in value]
                        value_str = "[" + ", ".join(inner_items) + "]"
                else:
                    value_str = custom_format(value, indent + 4)
            else:
                value_str = custom_format(value, indent + 4)
                
            result += f"{spaces}    '{key}': {value_str}"
            if i < len(keys) - 1:
                result += ","
            result += "\n"
            
        result += spaces + "}"
        return result
    else:
        # Simple value
        return repr(obj)

def main():
    # Import the raw character definitions
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from chars import CHARACTERS_RAW
        from icons import ICONS_RAW
    except ImportError:
        print("Error: Could not import CHARACTERS_RAW from chars.py")
        return
    
    # Create compressed definitions
    compressed_chars = []
    
    for char in CHARACTERS_RAW:
        compressed_char = {
            "id": char["id"],
            "name": char["name"],
            "body": pattern_to_hex(char["body"])
        }
        
        # Handle highlight if present
        if "hl" in char:
            compressed_char["hl"] = pattern_to_hex(char["hl"])
            
        # Handle shadow if present
        if "sdw" in char:
            compressed_char["sdw"] = pattern_to_hex(char["sdw"])
            
        # Handle custom pixels - compress format
        if "custom" in char:
            compressed_char["custom"] = []
            for pixel in char["custom"]:
                compressed_char["custom"].append(
                    [pixel['col'], pixel['row'], pixel['color']]
                )
                
        # Handle animations - compress format
        if "animations" in char:
            compressed_char["animations"] = []
            for anim in char["animations"]:
                compressed_anim = [
                    anim["name"],                                 # Index 0: name
                    anim["interval"],                             # Index 1: interval
                    anim["frame_duration"],                       # Index 2: frame_duration
                    compress_frames(anim["frames"]),              # Index 3: frames
                    anim.get("color", (255, 255, 255)),          # Index 4: color
                    anim.get("reverse", False)                    # Index 5: reverse
                ]
                compressed_char["animations"].append(compressed_anim)

        compressed_chars.append(compressed_char)

    # Create compressed icons
    compressed_icons = []
    for icon in ICONS_RAW:
        compressed_icon = {
            "id": icon["id"],
            "name": icon["name"],
            "body": pattern_to_hex(icon["body"])
        }
        
        # Handle body_color if present - ONLY FOR ICONS
        if "body_color" in icon:
            compressed_icon["body_color"] = icon["body_color"]
        
        # Handle highlight if present
        if "hl" in icon:
            compressed_icon["hl"] = pattern_to_hex(icon["hl"])
            
        # Handle shadow if present
        if "sdw" in icon:
            compressed_icon["sdw"] = pattern_to_hex(icon["sdw"])
            
        # Handle custom pixels
        if "custom" in icon:
            compressed_icon["custom"] = []
            for pixel in icon["custom"]:
                compressed_icon["custom"].append(
                    [pixel['col'], pixel['row'], pixel['color']]
                )
                
        # Handle animations
        if "animations" in icon:
            compressed_icon["animations"] = []
            for anim in icon["animations"]:
                compressed_anim = [
                    anim["name"],
                    anim["interval"],
                    anim["frame_duration"],
                    compress_frames(anim["frames"]),
                    anim.get("color", (255, 255, 255)),
                    anim.get("reverse", False)
                ]
                compressed_icon["animations"].append(compressed_anim)

        compressed_icons.append(compressed_icon)
    
    # Format with our custom formatter
    output_content = "# Auto-generated from build_chars.py\n\n"
    output_content += "CHARACTERS_RAW = "
    output_content += custom_format(compressed_chars)
    
    # Write to output.py
    with open("output.py", "w") as f:
        f.write(output_content)
    
    print(f"Successfully compressed {len(compressed_chars)} characters")
    print("Output written to output.py")

    # Now inject the compressed character data into main.py
    try:
        with open("../main.py", "r") as f:
            main_content = f.read()
        
        # Handle characters
        start_marker = "# BEGIN COMPRESSED CHARACTER DATA"
        end_marker = "# END COMPRESSED CHARACTER DATA"
        
        start_index = main_content.find(start_marker)
        end_index = main_content.find(end_marker)
        
        if start_index != -1 and end_index != -1:
            end_index += len(end_marker)
            new_section = f"{start_marker}\nCHARACTERS_RAW = {custom_format(compressed_chars)}\n{end_marker}"
            main_content = main_content[:start_index] + new_section + main_content[end_index:]
        
        # Handle icons (new section)
        icon_start_marker = "# BEGIN COMPRESSED ICON DATA"
        icon_end_marker = "# END COMPRESSED ICON DATA"
        
        icon_start_index = main_content.find(icon_start_marker)
        icon_end_index = main_content.find(icon_end_marker)
        
        if icon_start_index != -1 and icon_end_index != -1:
            icon_end_index += len(icon_end_marker)
            new_icon_section = f"{icon_start_marker}\nICONS_RAW = {custom_format(compressed_icons)}\n{icon_end_marker}"
            main_content = main_content[:icon_start_index] + new_icon_section + main_content[icon_end_index:]
            
        with open("../main.py", "w") as f:
            f.write(main_content)
            
        print("Successfully injected compressed data into main.py")
    except Exception as e:
        print(f"Error updating main.py: {e}")
    
    # Calculate size differences
    import json
    raw_size = len(str(CHARACTERS_RAW))
    compressed_size = len(str(compressed_chars))
    compression_ratio = (1 - compressed_size / raw_size) * 100
    
    print(f"Raw size: {raw_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {compression_ratio:.1f}%")
    
    # Also print the output for immediate copy-paste
    print("\n--- COPY BELOW THIS LINE ---\n")
    print(output_content)
    print("\n--- COPY ABOVE THIS LINE ---\n")

if __name__ == "__main__":
    main()