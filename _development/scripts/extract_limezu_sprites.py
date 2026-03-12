#!/usr/bin/env python3
"""
Extract LimeZu sprites from spritesheets + generate themed Pillow sprites.
Outputs mc_v2_part1_sprites.js with PNG base64 constants for Mission Control v3.

Usage: python _development/scripts/extract_limezu_sprites.py

Source assets:
  - Modern tiles_Free/Interiors_free/16x16/Interiors_free_16x16.png (256x1424, 16x89 grid)
  - Modern tiles_Free/Interiors_free/16x16/Room_Builder_free_16x16.png (272x368, 17x23 grid)
  - interior free/interior free.png (160x80, rustic furniture)
"""

import base64
import io
import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

# ── Paths ────────────────────────────────────────────────────────────
DOWNLOADS = os.path.expanduser("~/Downloads")
INTERIORS_PATH = os.path.join(DOWNLOADS, "Modern tiles_Free", "Interiors_free", "16x16", "Interiors_free_16x16.png")
ROOM_BUILDER_PATH = os.path.join(DOWNLOADS, "Modern tiles_Free", "Interiors_free", "16x16", "Room_Builder_free_16x16.png")
INTERIOR_FREE_PATH = os.path.join(DOWNLOADS, "interior free", "interior free.png")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_runtime")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "mc_v2_part1_sprites.js")

# Also read existing part1 to preserve character PNGs, wall PNG, etc.
EXISTING_PART1 = os.path.join(OUTPUT_DIR, "mc_v2_part1_sprites.js")

TILE = 16  # tile size in pixels


# ── Helper Functions ─────────────────────────────────────────────────

def crop_tile(img, col, row, w=1, h=1):
    """Crop a region from spritesheet. w,h in tile units."""
    x1 = col * TILE
    y1 = row * TILE
    x2 = x1 + w * TILE
    y2 = y1 + h * TILE
    return img.crop((x1, y1, x2, y2))


def to_base64(pil_img):
    """Convert PIL Image to data:image/png;base64,... string."""
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:image/png;base64,{b64}"


def is_empty_tile(img):
    """Check if a tile is fully transparent."""
    if img.mode != 'RGBA':
        return False
    pixels = list(img.getdata())
    return all(p[3] == 0 for p in pixels)


def scale_sprite(img, factor=2):
    """Scale up with nearest-neighbor for pixel art."""
    w, h = img.size
    return img.resize((w * factor, h * factor), Image.NEAREST)


# ── LimeZu Sprite Extraction ────────────────────────────────────────

def extract_limezu_sprites(interiors_img, room_builder_img):
    """Extract all needed sprites from LimeZu spritesheets.

    Returns dict of {name: PIL.Image} for each sprite.
    Multi-tile objects are cropped as single images.
    """
    sprites = {}

    # ────────────────────────────────────────────────────
    # DESKS (rows 3-9 of interiors spritesheet)
    # Each desk is 2 tiles wide x 1-2 tiles tall
    # ────────────────────────────────────────────────────

    # Executive desk: polished dark wood (row 3-4, col 0-1 area)
    # Row 3 has bed-like objects, rows 4-5 have tables
    # From preview_tables: green desk top-left, striped desk, light desk, dark desk
    sprites['desk_exec'] = crop_tile(interiors_img, 4, 3, 2, 2)  # Striped desk with drawers
    sprites['desk_war'] = crop_tile(interiors_img, 0, 5, 2, 2)   # Dark functional desk
    sprites['desk_gothic'] = crop_tile(interiors_img, 4, 5, 2, 2) # Wood desk variant
    sprites['desk_darklab'] = crop_tile(interiors_img, 0, 7, 2, 2) # Simple desk
    sprites['desk_demon'] = crop_tile(interiors_img, 4, 7, 2, 2)  # Basic light desk

    # ────────────────────────────────────────────────────
    # CHAIRS (rows 28-35)
    # Various chair styles 1x1 or 1x2
    # ────────────────────────────────────────────────────

    # Chairs: rows 28-29 are the main chair area (1x2 each)
    # Row 28-29 cols 0-1: chair style A, cols 2-3: style B, etc.
    # Row 31-32 cols 4-5, 6-7: counter chairs (2x2 blocks)
    # Row 33: counter/bar fronts with detail
    sprites['chair_exec'] = crop_tile(interiors_img, 0, 28, 1, 2)   # Elegant chair (cols 0)
    sprites['chair_war'] = crop_tile(interiors_img, 2, 28, 1, 2)    # Sturdy chair (col 2)
    sprites['chair_gothic'] = crop_tile(interiors_img, 7, 28, 1, 2) # Dark chair (col 7)
    sprites['chair_darklab'] = crop_tile(interiors_img, 9, 28, 1, 2) # Metal stool (col 9)
    sprites['chair_demon'] = crop_tile(interiors_img, 4, 28, 1, 2)  # Basic chair (col 4)

    # ────────────────────────────────────────────────────
    # BOOKSHELVES (rows 14-17)
    # 1 tile wide x 2 tiles tall
    # ────────────────────────────────────────────────────

    sprites['bookshelf_exec'] = crop_tile(interiors_img, 0, 14, 1, 2)   # Full bookshelf
    sprites['bookshelf_war'] = crop_tile(interiors_img, 2, 14, 1, 2)    # Bookshelf variant
    sprites['bookshelf_gothic'] = crop_tile(interiors_img, 4, 14, 1, 2) # Dark bookshelf
    sprites['bookshelf_darklab'] = crop_tile(interiors_img, 6, 14, 1, 2) # Sparse shelf
    sprites['bookshelf_demon'] = crop_tile(interiors_img, 8, 14, 1, 2)  # Basic shelf

    # ────────────────────────────────────────────────────
    # PAINTINGS / FRAMES (rows 17-20)
    # ────────────────────────────────────────────────────

    sprites['painting_exec'] = crop_tile(interiors_img, 0, 18, 2, 2)   # Large framed painting
    sprites['painting_war'] = crop_tile(interiors_img, 4, 18, 2, 2)    # Map/tactical board
    sprites['painting_gothic'] = crop_tile(interiors_img, 0, 20, 2, 2) # Dark painting

    # Small frames (1x1)
    sprites['frame_small_1'] = crop_tile(interiors_img, 8, 18, 1, 1)
    sprites['frame_small_2'] = crop_tile(interiors_img, 9, 18, 1, 1)
    sprites['frame_small_3'] = crop_tile(interiors_img, 10, 18, 1, 1)

    # ────────────────────────────────────────────────────
    # RUGS (rows 19-22) - 3x2 or 4x3 tiles
    # ────────────────────────────────────────────────────

    sprites['rug_exec'] = crop_tile(interiors_img, 6, 19, 4, 3)     # Ornate rug
    sprites['rug_gothic'] = crop_tile(interiors_img, 10, 19, 4, 3)  # Dark rug

    # ────────────────────────────────────────────────────
    # PLANTS (rows 36-38)
    # ────────────────────────────────────────────────────

    sprites['plant_potted_1'] = crop_tile(interiors_img, 6, 36, 1, 2)  # Tall potted plant
    sprites['plant_potted_2'] = crop_tile(interiors_img, 8, 36, 1, 2)  # Palm-like plant
    sprites['plant_small_1'] = crop_tile(interiors_img, 0, 36, 1, 1)   # Small plant
    sprites['plant_small_2'] = crop_tile(interiors_img, 2, 36, 1, 1)   # Another small plant
    sprites['plant_cactus'] = crop_tile(interiors_img, 4, 36, 1, 1)    # Cactus

    # ────────────────────────────────────────────────────
    # LAMPS (rows 44-47)
    # ────────────────────────────────────────────────────

    sprites['lamp_floor_1'] = crop_tile(interiors_img, 0, 44, 1, 2)    # Floor lamp
    sprites['lamp_floor_2'] = crop_tile(interiors_img, 2, 44, 1, 2)    # Floor lamp variant
    sprites['lamp_desk'] = crop_tile(interiors_img, 4, 44, 1, 1)       # Desk lamp
    sprites['lamp_mushroom'] = crop_tile(interiors_img, 0, 46, 1, 2)   # Mushroom lamp (gothic)

    # ────────────────────────────────────────────────────
    # SOFAS (rows 74-89 - end section, detailed multi-tile)
    # ────────────────────────────────────────────────────

    # Sofas from end section - multi-tile detailed sprites
    # Row 74: top parts at cols 0-6, 7-9
    # Row 75: bottom parts
    # Rows 77-83: more sofa variants at cols 3-10 (2-tile wide segments)
    sprites['sofa_gray'] = crop_tile(interiors_img, 1, 74, 3, 2)    # Gray sofa top section
    sprites['sofa_blue'] = crop_tile(interiors_img, 4, 74, 3, 2)    # Blue/teal sofa
    sprites['sofa_brown'] = crop_tile(interiors_img, 3, 77, 2, 2)   # Brown leather segment
    sprites['sofa_tan'] = crop_tile(interiors_img, 7, 77, 2, 2)     # Tan/beige segment

    # ────────────────────────────────────────────────────
    # WARDROBES / DOORS (rows 48-52)
    # ────────────────────────────────────────────────────

    sprites['wardrobe_1'] = crop_tile(interiors_img, 8, 48, 2, 2)   # Wooden wardrobe
    sprites['wardrobe_2'] = crop_tile(interiors_img, 10, 48, 2, 2)  # Another wardrobe
    sprites['door_1'] = crop_tile(interiors_img, 12, 48, 1, 2)      # Door

    # ────────────────────────────────────────────────────
    # KITCHEN APPLIANCES (rows 0-2)
    # ────────────────────────────────────────────────────

    # Kitchen appliances: row 0 has small items, rows 1-2 have larger ones
    sprites['fridge'] = crop_tile(interiors_img, 0, 1, 1, 2)       # Fridge (col 0, rows 1-2)
    sprites['microwave'] = crop_tile(interiors_img, 5, 1, 1, 2)    # Microwave on counter
    sprites['stove'] = crop_tile(interiors_img, 6, 1, 1, 2)        # Stove (col 6-7)
    sprites['sink'] = crop_tile(interiors_img, 9, 1, 1, 2)         # Sink

    # ────────────────────────────────────────────────────
    # VENDING MACHINES & MISC (rows 62-72)
    # ────────────────────────────────────────────────────

    # Vending machines at rows 66-69 (col 3 = 1x2 machine)
    sprites['vending_machine'] = crop_tile(interiors_img, 3, 66, 1, 2)  # Vending machine
    # Filing cabinet / storage rows 62-63 (various cols)
    sprites['filing_cabinet'] = crop_tile(interiors_img, 0, 62, 1, 2)   # Filing cabinet
    # Barrels/crates from storage area
    sprites['barrel'] = crop_tile(interiors_img, 4, 62, 1, 2)           # Barrel with stuff
    sprites['crate'] = crop_tile(interiors_img, 6, 62, 1, 2)            # Crate/storage
    # Aquarium from row 68-69 (cols 10-15 have shelving/display)
    sprites['aquarium'] = crop_tile(interiors_img, 10, 68, 2, 2)        # Aquarium/display
    sprites['globe'] = crop_tile(interiors_img, 10, 38, 1, 1)           # Globe

    # ────────────────────────────────────────────────────
    # WINDOWS & CURTAINS (rows 21-27)
    # ────────────────────────────────────────────────────

    sprites['window_1'] = crop_tile(interiors_img, 0, 22, 2, 2)    # Open window
    sprites['window_2'] = crop_tile(interiors_img, 4, 22, 2, 2)    # Window with blinds
    sprites['curtain_open'] = crop_tile(interiors_img, 0, 26, 1, 2)  # Open curtain
    sprites['curtain_closed'] = crop_tile(interiors_img, 2, 26, 1, 2) # Closed curtain

    # ────────────────────────────────────────────────────
    # COUNTERS / BAR (rows 32-35)
    # ────────────────────────────────────────────────────

    sprites['counter_wood'] = crop_tile(interiors_img, 0, 32, 1, 2)   # Wood counter piece
    sprites['counter_dark'] = crop_tile(interiors_img, 4, 32, 1, 2)   # Dark counter

    # ────────────────────────────────────────────────────
    # CLASSROOM (rows 38-42)
    # ────────────────────────────────────────────────────

    sprites['school_desk'] = crop_tile(interiors_img, 0, 38, 1, 2)    # School desk
    sprites['blackboard'] = crop_tile(interiors_img, 4, 38, 2, 2)     # Blackboard
    sprites['globe_stand'] = crop_tile(interiors_img, 10, 38, 1, 1)   # Globe on stand

    # ────────────────────────────────────────────────────
    # WHITEBOARD from preview area
    # ────────────────────────────────────────────────────

    sprites['whiteboard'] = crop_tile(interiors_img, 8, 40, 2, 2)   # Whiteboard/chalkboard

    # ────────────────────────────────────────────────────
    # CHESTS / TRUNKS (rows 86-89)
    # ────────────────────────────────────────────────────

    sprites['chest_wood'] = crop_tile(interiors_img, 0, 86, 1, 1)     # Wooden chest
    sprites['chest_fancy'] = crop_tile(interiors_img, 2, 86, 1, 1)    # Fancy chest

    # ════════════════════════════════════════════════════
    # ROOM BUILDER - FLOORS & WALLS
    # ════════════════════════════════════════════════════

    # Floor tiles (right side of Room Builder, col 11+)
    # Each floor pattern is typically a 2x2 or 3x3 block

    # Floor patterns from Room Builder
    sprites['floor_wood_light'] = crop_tile(room_builder_img, 0, 5, 4, 2)    # Light wood planks
    sprites['floor_wood_dark'] = crop_tile(room_builder_img, 0, 7, 4, 2)     # Dark wood planks
    sprites['floor_wood_red'] = crop_tile(room_builder_img, 0, 9, 4, 2)      # Reddish wood
    sprites['floor_wood_orange'] = crop_tile(room_builder_img, 0, 11, 4, 2)  # Orange wood
    sprites['floor_wood_white'] = crop_tile(room_builder_img, 0, 13, 4, 2)   # White/bleached
    sprites['floor_wood_purple'] = crop_tile(room_builder_img, 0, 15, 4, 2)  # Purple-tinted
    sprites['floor_wood_beige'] = crop_tile(room_builder_img, 0, 17, 4, 2)   # Beige/cream
    sprites['floor_wood_gray'] = crop_tile(room_builder_img, 0, 19, 4, 2)    # Gray wood

    # Decorative floor tiles (right side col 11-16)
    sprites['floor_tile_red'] = crop_tile(room_builder_img, 11, 5, 3, 3)     # Red brick/tile
    sprites['floor_tile_cream'] = crop_tile(room_builder_img, 14, 5, 3, 3)   # Cream tiles
    sprites['floor_tile_blue'] = crop_tile(room_builder_img, 11, 8, 3, 3)    # Blue circle tiles
    sprites['floor_tile_gray'] = crop_tile(room_builder_img, 14, 8, 3, 3)    # Gray stone
    sprites['floor_tile_herring'] = crop_tile(room_builder_img, 11, 11, 3, 3)  # Herringbone
    sprites['floor_tile_marble'] = crop_tile(room_builder_img, 14, 11, 3, 3)   # Marble/neutral

    # Wall segments from Room Builder (left side, 4 cols wide, 2 rows each)
    sprites['wall_orange'] = crop_tile(room_builder_img, 4, 5, 4, 2)    # Orange/warm walls
    sprites['wall_cream'] = crop_tile(room_builder_img, 4, 7, 4, 2)     # Cream walls
    sprites['wall_cyan'] = crop_tile(room_builder_img, 4, 9, 4, 2)      # Cyan/teal walls
    sprites['wall_tan'] = crop_tile(room_builder_img, 4, 11, 4, 2)      # Tan walls
    sprites['wall_purple'] = crop_tile(room_builder_img, 4, 13, 4, 2)   # Purple walls
    sprites['wall_dark'] = crop_tile(room_builder_img, 4, 15, 4, 2)     # Dark wood walls
    sprites['wall_gray'] = crop_tile(room_builder_img, 4, 17, 4, 2)     # Gray walls
    sprites['wall_light'] = crop_tile(room_builder_img, 4, 19, 4, 2)    # Light/white walls

    return sprites


# ── Pillow-Generated Themed Sprites ─────────────────────────────────

def generate_pillow_sprites():
    """Generate themed sprites that LimeZu doesn't cover.
    Uses Pillow for rich pixel-art with gradients and texture."""

    sprites = {}

    # ── PC / MONITOR (16x16) ─────────────────────────────

    def make_pc(screen_color, frame_color, stand_color, highlight):
        """Generate a PC monitor sprite."""
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Monitor frame
        d.rectangle([2, 1, 13, 9], fill=frame_color)
        d.rectangle([3, 2, 12, 8], fill=screen_color)
        # Screen highlight
        d.line([4, 3, 7, 3], fill=highlight)
        d.line([4, 4, 5, 4], fill=highlight)
        # Stand
        d.rectangle([6, 10, 9, 11], fill=stand_color)
        d.rectangle([4, 12, 11, 12], fill=stand_color)
        # Keyboard
        d.rectangle([3, 14, 12, 15], fill=(80, 80, 90, 255))
        d.rectangle([4, 14, 11, 14], fill=(100, 100, 115, 255))
        # Key dots
        for kx in range(5, 11, 2):
            d.point((kx, 14), fill=(130, 130, 145, 255))
        return img

    sprites['pc_exec'] = make_pc((30, 80, 60, 255), (50, 50, 55, 255), (60, 60, 65, 255), (60, 130, 90, 255))
    sprites['pc_war'] = make_pc((20, 60, 20, 255), (50, 55, 40, 255), (70, 65, 45, 255), (50, 120, 50, 255))
    sprites['pc_gothic'] = make_pc((50, 20, 60, 255), (40, 30, 45, 255), (55, 40, 55, 255), (100, 50, 120, 255))
    sprites['pc_darklab'] = make_pc((60, 20, 15, 255), (35, 35, 35, 255), (45, 45, 45, 255), (130, 40, 30, 255))
    sprites['pc_demon'] = make_pc((40, 60, 80, 255), (55, 55, 60, 255), (65, 65, 70, 255), (80, 120, 160, 255))

    # ── ARSENAL / WEAPONS RACK (16x32) - War theme ───────

    def make_arsenal():
        img = Image.new('RGBA', (16, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Wall mount rack (wood)
        d.rectangle([1, 2, 14, 29], fill=(80, 55, 30, 255))
        d.rectangle([2, 3, 13, 28], fill=(100, 70, 40, 255))
        # Horizontal shelf bars
        for sy in [6, 13, 20]:
            d.line([2, sy, 13, sy], fill=(70, 48, 25, 255))
        # Rifle 1
        d.line([4, 4, 4, 5], fill=(60, 60, 65, 255))
        d.line([4, 4, 11, 4], fill=(90, 90, 100, 255))
        d.rectangle([9, 3, 11, 5], fill=(80, 55, 35, 255))
        # Rifle 2
        d.line([4, 8, 11, 8], fill=(85, 85, 95, 255))
        d.rectangle([9, 7, 11, 9], fill=(75, 50, 30, 255))
        d.line([4, 8, 4, 9], fill=(55, 55, 60, 255))
        # Pistol
        d.rectangle([5, 14, 8, 16], fill=(70, 70, 80, 255))
        d.rectangle([5, 16, 6, 18], fill=(65, 45, 30, 255))
        # Knife
        d.line([10, 14, 10, 19], fill=(170, 175, 180, 255))
        d.line([10, 18, 10, 19], fill=(90, 60, 35, 255))
        # Ammo boxes
        d.rectangle([3, 22, 7, 25], fill=(60, 70, 50, 255))
        d.rectangle([4, 22, 6, 24], fill=(75, 85, 60, 255))
        d.rectangle([9, 22, 12, 25], fill=(65, 75, 55, 255))
        d.rectangle([10, 22, 11, 24], fill=(80, 90, 65, 255))
        # Grenade
        d.ellipse([5, 26, 7, 28], fill=(60, 70, 50, 255))
        d.line([6, 25, 6, 26], fill=(100, 100, 80, 255))
        return img

    sprites['arsenal'] = make_arsenal()

    # ── RADAR SCREEN (16x16) - War theme ─────────────────

    def make_radar():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Monitor case
        d.rectangle([1, 1, 14, 13], fill=(50, 55, 45, 255))
        d.rectangle([2, 2, 13, 12], fill=(10, 30, 10, 255))
        # Radar circles
        d.ellipse([3, 3, 12, 11], outline=(0, 80, 0, 255))
        d.ellipse([5, 5, 10, 9], outline=(0, 60, 0, 255))
        # Center dot
        d.point((7, 7), fill=(0, 200, 0, 255))
        d.point((8, 7), fill=(0, 200, 0, 255))
        # Sweep line
        d.line([8, 7, 12, 4], fill=(0, 180, 0, 200))
        # Blips
        d.point((5, 4), fill=(0, 255, 0, 255))
        d.point((10, 9), fill=(0, 220, 0, 255))
        # Stand
        d.rectangle([5, 14, 10, 15], fill=(60, 65, 55, 255))
        return img

    sprites['radar'] = make_radar()

    # ── RADIO MILITARY (16x16) - War theme ───────────────

    def make_radio():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Body
        d.rectangle([3, 4, 12, 14], fill=(60, 70, 50, 255))
        d.rectangle([4, 5, 11, 13], fill=(70, 80, 60, 255))
        # Antenna
        d.line([10, 1, 10, 4], fill=(100, 100, 90, 255))
        d.point((10, 0), fill=(200, 50, 50, 255))
        # Dial/display
        d.rectangle([5, 6, 10, 8], fill=(20, 40, 20, 255))
        d.line([6, 7, 9, 7], fill=(0, 150, 0, 255))
        # Knobs
        d.ellipse([5, 10, 7, 12], fill=(50, 55, 40, 255))
        d.ellipse([9, 10, 11, 12], fill=(50, 55, 40, 255))
        return img

    sprites['radio_military'] = make_radio()

    # ── SANDBAGS (16x16) - War theme ─────────────────────

    def make_sandbags():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Bottom row of bags
        d.rounded_rectangle([0, 10, 6, 15], radius=2, fill=(160, 140, 90, 255))
        d.rounded_rectangle([5, 10, 11, 15], radius=2, fill=(150, 130, 85, 255))
        d.rounded_rectangle([10, 10, 15, 15], radius=2, fill=(155, 135, 88, 255))
        # Top row
        d.rounded_rectangle([2, 5, 8, 10], radius=2, fill=(165, 145, 95, 255))
        d.rounded_rectangle([7, 5, 13, 10], radius=2, fill=(155, 135, 90, 255))
        # Ties
        d.line([3, 7, 3, 8], fill=(100, 80, 50, 255))
        d.line([10, 7, 10, 8], fill=(100, 80, 50, 255))
        d.line([3, 12, 3, 13], fill=(100, 80, 50, 255))
        d.line([8, 12, 8, 13], fill=(100, 80, 50, 255))
        d.line([13, 12, 13, 13], fill=(100, 80, 50, 255))
        return img

    sprites['sandbags'] = make_sandbags()

    # ── CANDELABRA (16x24) - Gothic theme ────────────────

    def make_candelabra():
        img = Image.new('RGBA', (16, 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Base
        d.rectangle([5, 20, 10, 23], fill=(60, 50, 40, 255))
        d.rectangle([6, 18, 9, 20], fill=(80, 65, 45, 255))
        # Main stem
        d.line([7, 8, 7, 18], fill=(90, 75, 50, 255))
        d.line([8, 8, 8, 18], fill=(100, 85, 55, 255))
        # Arms
        d.line([3, 8, 7, 8], fill=(90, 75, 50, 255))
        d.line([8, 8, 12, 8], fill=(90, 75, 50, 255))
        # Candle holders
        for cx in [3, 7, 12]:
            d.rectangle([cx, 5, cx+1, 8], fill=(230, 220, 200, 255))  # Candle
            # Flame
            d.point((cx, 4), fill=(255, 200, 50, 255))
            d.point((cx+1, 4), fill=(255, 180, 30, 255))
            d.point((cx, 3), fill=(255, 230, 100, 255))
        # Dripping wax
        d.point((3, 6), fill=(220, 210, 190, 255))
        d.point((12, 7), fill=(220, 210, 190, 255))
        return img

    sprites['candelabra'] = make_candelabra()

    # ── SKULL ON BOOKS (16x16) - Gothic theme ────────────

    def make_skull_books():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Stack of books
        d.rectangle([2, 10, 13, 12], fill=(100, 30, 30, 255))  # Red book
        d.rectangle([2, 12, 13, 14], fill=(40, 60, 100, 255))  # Blue book
        d.rectangle([3, 14, 12, 15], fill=(60, 40, 80, 255))   # Purple book
        # Book spines detail
        d.line([2, 11, 13, 11], fill=(120, 40, 40, 255))
        d.line([2, 13, 13, 13], fill=(50, 70, 120, 255))
        # Skull
        d.ellipse([4, 3, 11, 10], fill=(230, 225, 215, 255))
        d.ellipse([5, 4, 10, 9], fill=(240, 235, 225, 255))
        # Eye sockets
        d.ellipse([5, 5, 7, 7], fill=(30, 25, 20, 255))
        d.ellipse([8, 5, 10, 7], fill=(30, 25, 20, 255))
        # Nose
        d.point((7, 8), fill=(40, 35, 30, 255))
        # Jaw
        d.line([6, 9, 9, 9], fill=(210, 205, 195, 255))
        return img

    sprites['skull_books'] = make_skull_books()

    # ── POTION BOTTLES (16x16) - Gothic theme ────────────

    def make_potions():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Shelf plank
        d.rectangle([0, 13, 15, 15], fill=(100, 70, 40, 255))
        d.line([0, 13, 15, 13], fill=(120, 85, 50, 255))
        # Bottle 1 (green)
        d.rectangle([1, 7, 4, 13], fill=(40, 150, 60, 180))
        d.rectangle([2, 5, 3, 7], fill=(40, 150, 60, 200))
        d.point((2, 4), fill=(80, 70, 60, 255))
        d.line([2, 8, 3, 8], fill=(60, 200, 80, 200))
        # Bottle 2 (purple)
        d.ellipse([5, 8, 9, 13], fill=(120, 40, 160, 180))
        d.rectangle([6, 5, 8, 8], fill=(120, 40, 160, 200))
        d.point((7, 4), fill=(80, 70, 60, 255))
        # Bottle 3 (red)
        d.rectangle([10, 9, 14, 13], fill=(180, 30, 30, 180))
        d.rectangle([11, 6, 13, 9], fill=(180, 30, 30, 200))
        d.point((12, 5), fill=(80, 70, 60, 255))
        d.line([11, 10, 13, 10], fill=(220, 50, 50, 200))
        return img

    sprites['potions'] = make_potions()

    # ── ANTIQUE CLOCK (16x16) - Gothic theme ─────────────

    def make_clock():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Frame
        d.ellipse([2, 1, 13, 12], fill=(80, 55, 35, 255))
        d.ellipse([3, 2, 12, 11], fill=(100, 75, 45, 255))
        # Face
        d.ellipse([4, 3, 11, 10], fill=(240, 235, 220, 255))
        # Hour marks
        for angle in range(12):
            rad = angle * math.pi / 6
            mx = int(7.5 + 2.8 * math.sin(rad))
            my = int(6.5 - 2.8 * math.cos(rad))
            d.point((mx, my), fill=(40, 30, 20, 255))
        # Hands
        d.line([7, 6, 7, 4], fill=(30, 20, 10, 255))  # Hour
        d.line([7, 6, 10, 6], fill=(30, 20, 10, 255))  # Minute
        d.point((7, 6), fill=(180, 30, 30, 255))  # Center
        # Pendulum area
        d.rectangle([6, 12, 9, 15], fill=(80, 55, 35, 255))
        d.ellipse([6, 13, 9, 15], fill=(200, 180, 50, 255))
        return img

    sprites['antique_clock'] = make_clock()

    # ── CAULDRON (16x16) - Darklab/Terror theme ──────────

    def make_cauldron():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Legs (tripod)
        d.line([3, 14, 4, 12], fill=(50, 45, 40, 255))
        d.line([12, 14, 11, 12], fill=(50, 45, 40, 255))
        d.line([7, 15, 7, 13], fill=(50, 45, 40, 255))
        # Cauldron body
        d.ellipse([2, 6, 13, 14], fill=(40, 40, 45, 255))
        d.ellipse([3, 7, 12, 13], fill=(55, 55, 60, 255))
        # Rim
        d.arc([2, 5, 13, 9], 180, 360, fill=(70, 70, 75, 255))
        # Green liquid surface
        d.ellipse([3, 5, 12, 9], fill=(30, 120, 40, 200))
        d.ellipse([4, 6, 11, 8], fill=(50, 160, 60, 200))
        # Bubbles
        d.ellipse([5, 5, 7, 7], fill=(60, 200, 70, 180))
        d.point((9, 6), fill=(80, 220, 90, 200))
        d.point((6, 4), fill=(40, 180, 50, 150))
        # Steam wisps
        d.point((5, 3), fill=(60, 180, 70, 100))
        d.point((8, 2), fill=(60, 180, 70, 80))
        d.point((10, 3), fill=(60, 180, 70, 60))
        d.point((7, 1), fill=(60, 180, 70, 40))
        return img

    sprites['cauldron'] = make_cauldron()

    # ── BONES (16x16) - Darklab/Terror theme ─────────────

    def make_bones():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Crossed bones
        d.line([2, 3, 13, 12], fill=(230, 225, 210, 255), width=1)
        d.line([13, 3, 2, 12], fill=(230, 225, 210, 255), width=1)
        # Bone ends (knobs)
        d.ellipse([1, 2, 3, 4], fill=(235, 230, 215, 255))
        d.ellipse([12, 1, 14, 3], fill=(235, 230, 215, 255))
        d.ellipse([1, 11, 3, 13], fill=(235, 230, 215, 255))
        d.ellipse([12, 11, 14, 13], fill=(235, 230, 215, 255))
        # Small skull
        d.ellipse([5, 5, 10, 10], fill=(240, 235, 220, 255))
        d.point((6, 7), fill=(30, 25, 20, 255))
        d.point((9, 7), fill=(30, 25, 20, 255))
        d.line([7, 9, 8, 9], fill=(210, 205, 195, 255))
        return img

    sprites['bones'] = make_bones()

    # ── SPIDER WEB (16x16) - Darklab/Terror theme ────────

    def make_spiderweb():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Radial lines from corner
        web_color = (200, 200, 210, 160)
        d.line([0, 0, 15, 15], fill=web_color)
        d.line([0, 0, 15, 8], fill=web_color)
        d.line([0, 0, 8, 15], fill=web_color)
        d.line([0, 0, 15, 3], fill=web_color)
        d.line([0, 0, 3, 15], fill=web_color)
        d.line([0, 0, 15, 0], fill=web_color)
        d.line([0, 0, 0, 15], fill=web_color)
        # Concentric arcs
        d.arc([0, 0, 10, 10], 0, 90, fill=(200, 200, 210, 120))
        d.arc([0, 0, 20, 20], 0, 90, fill=(200, 200, 210, 100))
        # Spider
        d.point((8, 8), fill=(40, 35, 30, 255))
        d.point((7, 7), fill=(50, 45, 40, 255))
        return img

    sprites['spiderweb'] = make_spiderweb()

    # ── TEST TUBES (16x16) - Darklab theme ───────────────

    def make_test_tubes():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Rack
        d.rectangle([1, 3, 14, 5], fill=(120, 120, 130, 255))
        d.rectangle([1, 3, 14, 4], fill=(140, 140, 150, 255))
        d.rectangle([2, 13, 13, 15], fill=(100, 100, 110, 255))
        # Tube 1 (green)
        d.rectangle([3, 5, 4, 13], fill=(180, 200, 190, 150))
        d.rectangle([3, 8, 4, 13], fill=(40, 180, 60, 180))
        d.point((3, 2), fill=(100, 100, 110, 255))
        # Tube 2 (purple)
        d.rectangle([6, 5, 7, 13], fill=(180, 180, 200, 150))
        d.rectangle([6, 9, 7, 13], fill=(140, 40, 180, 180))
        d.point((6, 2), fill=(100, 100, 110, 255))
        # Tube 3 (red)
        d.rectangle([9, 5, 10, 13], fill=(200, 180, 180, 150))
        d.rectangle([9, 7, 10, 13], fill=(200, 40, 40, 180))
        d.point((9, 2), fill=(100, 100, 110, 255))
        # Tube 4 (yellow)
        d.rectangle([12, 5, 13, 13], fill=(200, 200, 180, 150))
        d.rectangle([12, 10, 13, 13], fill=(220, 200, 40, 180))
        d.point((12, 2), fill=(100, 100, 110, 255))
        return img

    sprites['test_tubes'] = make_test_tubes()

    # ── CARDBOARD BOX (16x16) - Demonetized theme ────────

    def make_cardboard_box():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Box body
        d.rectangle([2, 6, 13, 15], fill=(180, 150, 100, 255))
        d.rectangle([3, 7, 12, 14], fill=(195, 165, 115, 255))
        # Top flaps (open)
        d.polygon([(2, 6), (1, 3), (5, 5), (7, 6)], fill=(190, 160, 110, 255))
        d.polygon([(13, 6), (14, 3), (10, 5), (8, 6)], fill=(185, 155, 105, 255))
        # Tape
        d.line([7, 6, 7, 15], fill=(170, 150, 90, 200))
        d.line([8, 6, 8, 15], fill=(175, 155, 95, 200))
        # Crease marks
        d.line([3, 10, 12, 10], fill=(170, 140, 95, 255))
        return img

    sprites['cardboard_box'] = make_cardboard_box()

    # ── DESK FAN (16x16) - Demonetized theme ─────────────

    def make_desk_fan():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Base
        d.rectangle([4, 13, 11, 15], fill=(80, 80, 90, 255))
        d.rectangle([5, 13, 10, 14], fill=(95, 95, 105, 255))
        # Neck
        d.rectangle([7, 10, 8, 13], fill=(90, 90, 100, 255))
        # Fan cage circle
        d.ellipse([2, 1, 13, 11], outline=(100, 100, 110, 255))
        d.ellipse([3, 2, 12, 10], outline=(110, 110, 120, 255))
        # Fan blades (motion blur effect)
        center_x, center_y = 7, 6
        d.line([center_x, center_y, 3, 3], fill=(160, 165, 170, 180))
        d.line([center_x, center_y, 11, 3], fill=(160, 165, 170, 180))
        d.line([center_x, center_y, 3, 9], fill=(160, 165, 170, 180))
        d.line([center_x, center_y, 11, 9], fill=(160, 165, 170, 180))
        # Center hub
        d.ellipse([6, 5, 9, 7], fill=(70, 70, 80, 255))
        return img

    sprites['desk_fan'] = make_desk_fan()

    # ── COFFEE MUG (16x16) - Demonetized theme ───────────

    def make_coffee_mug():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Mug body
        d.rectangle([4, 6, 10, 14], fill=(220, 220, 230, 255))
        d.rectangle([5, 7, 9, 13], fill=(235, 235, 240, 255))
        # Handle
        d.arc([9, 8, 13, 12], -90, 90, fill=(210, 210, 220, 255))
        # Coffee surface
        d.rectangle([5, 7, 9, 8], fill=(90, 55, 30, 255))
        d.line([5, 7, 9, 7], fill=(110, 70, 40, 255))
        # Steam wisps
        d.point((6, 4), fill=(200, 200, 210, 120))
        d.point((7, 3), fill=(200, 200, 210, 80))
        d.point((8, 5), fill=(200, 200, 210, 100))
        d.point((7, 2), fill=(200, 200, 210, 50))
        # Saucer
        d.rectangle([3, 14, 11, 15], fill=(210, 210, 220, 255))
        return img

    sprites['coffee_mug'] = make_coffee_mug()

    # ── MOTIVATIONAL POSTER (16x16) - Demonetized theme ──

    def make_poster():
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Frame
        d.rectangle([2, 1, 13, 14], fill=(180, 175, 165, 255))
        d.rectangle([3, 2, 12, 13], fill=(245, 240, 230, 255))
        # Sunset image (top)
        d.rectangle([3, 2, 12, 7], fill=(70, 130, 180, 255))
        d.rectangle([3, 5, 12, 7], fill=(220, 120, 50, 255))
        d.ellipse([6, 3, 9, 6], fill=(255, 200, 50, 255))
        # Text area (bottom)
        d.line([4, 9, 11, 9], fill=(80, 80, 80, 255))
        d.line([5, 11, 10, 11], fill=(120, 120, 120, 255))
        return img

    sprites['poster'] = make_poster()

    # ── TROPHY (16x24) - Executive theme ─────────────────

    def make_trophy():
        img = Image.new('RGBA', (16, 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Base (marble)
        d.rectangle([3, 19, 12, 23], fill=(60, 55, 50, 255))
        d.rectangle([4, 19, 11, 22], fill=(80, 75, 65, 255))
        d.line([4, 19, 11, 19], fill=(100, 95, 85, 255))
        # Stem
        d.rectangle([6, 14, 9, 19], fill=(220, 190, 60, 255))
        d.rectangle([7, 14, 8, 19], fill=(240, 210, 80, 255))
        # Cup
        d.rectangle([3, 5, 12, 14], fill=(210, 180, 50, 255))
        d.rectangle([4, 6, 11, 13], fill=(230, 200, 70, 255))
        d.rectangle([5, 7, 10, 12], fill=(240, 215, 90, 255))
        # Handles
        d.arc([1, 7, 4, 11], 90, 270, fill=(200, 170, 40, 255))
        d.arc([11, 7, 14, 11], -90, 90, fill=(200, 170, 40, 255))
        # Star emblem
        d.point((7, 9), fill=(255, 240, 120, 255))
        d.point((8, 9), fill=(255, 240, 120, 255))
        d.point((7, 8), fill=(255, 240, 120, 255))
        d.point((8, 8), fill=(255, 240, 120, 255))
        # Rim highlight
        d.line([4, 6, 11, 6], fill=(250, 230, 100, 255))
        return img

    sprites['trophy'] = make_trophy()

    # ── STAINED TABLE (32x32) - Darklab theme ────────────

    def make_lab_table():
        """Lab table with stains - replaces standard desk for darklab."""
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Table top
        d.rectangle([1, 4, 30, 22], fill=(70, 75, 80, 255))
        d.rectangle([2, 5, 29, 21], fill=(85, 90, 95, 255))
        d.line([2, 5, 29, 5], fill=(100, 105, 110, 255))
        # Surface texture lines
        for i in range(3, 28, 4):
            d.line([i, 6, i, 20], fill=(78, 83, 88, 255))
        # Stains
        d.ellipse([5, 8, 10, 13], fill=(60, 80, 55, 200))
        d.ellipse([18, 10, 22, 14], fill=(100, 40, 40, 180))
        d.ellipse([12, 15, 16, 18], fill=(50, 70, 50, 160))
        # Legs
        d.rectangle([3, 22, 5, 28], fill=(60, 65, 70, 255))
        d.rectangle([26, 22, 28, 28], fill=(60, 65, 70, 255))
        d.rectangle([3, 22, 5, 23], fill=(75, 80, 85, 255))
        d.rectangle([26, 22, 28, 23], fill=(75, 80, 85, 255))
        return img

    sprites['lab_table'] = make_lab_table()

    return sprites


# ── Floor Tile Generators ────────────────────────────────────────────

def make_floor_tile_single(room_builder_img, subnicho):
    """Extract a single 16x16 floor tile from Room Builder for each subnicho.
    This is the repeating pattern used to fill room floors."""

    if subnicho == 'executive':
        # Elegant terracotta/tile from right side
        return crop_tile(room_builder_img, 12, 6, 1, 1)
    elif subnicho == 'warroom':
        # Gray stone
        return crop_tile(room_builder_img, 15, 9, 1, 1)
    elif subnicho == 'gothic':
        # Dark wood
        return crop_tile(room_builder_img, 1, 7, 1, 1)
    elif subnicho == 'darklab':
        # Dark stone/herringbone
        return crop_tile(room_builder_img, 12, 12, 1, 1)
    elif subnicho == 'demonetized':
        # Simple light wood
        return crop_tile(room_builder_img, 1, 5, 1, 1)
    else:
        return crop_tile(room_builder_img, 1, 5, 1, 1)


# ── Build Output JS ─────────────────────────────────────────────────

def build_js_output(all_sprites, floor_tiles, existing_js):
    """Build the complete mc_v2_part1_sprites.js with PNG base64 constants.

    Preserves: constants, direction enum, character system, wall system.
    Replaces: hex-array furniture sprites with PNG base64 references.
    Adds: FURNITURE_PNGS, FLOOR_PNGS objects.
    """

    lines = []

    # ── Header ──
    lines.append("// ============================================================")
    lines.append("// Mission Control v3 - Part 1: Sprite Data & Cache System")
    lines.append("// Source: LimeZu tilesets + Pillow-generated themed sprites")
    lines.append("// ============================================================")
    lines.append("")

    # ── Constants (preserved from original) ──
    lines.append("// -- Constants -----------------------------------------------")
    lines.append("const TILE_SIZE = 16;")
    lines.append("const WALK_SPEED = 48;")
    lines.append("const WALK_FRAME_DUR = 0.15;")
    lines.append("const TYPE_FRAME_DUR = 0.3;")
    lines.append("const SIT_OFFSET = 6;")
    lines.append("const _ = '';")
    lines.append("")
    lines.append("// -- Direction enum ------------------------------------------")
    lines.append("const Direction = { DOWN: 0, LEFT: 1, RIGHT: 2, UP: 3 };")
    lines.append("")

    # ── FURNITURE PNGs (base64) ──
    lines.append("// -- Furniture PNG Sprites (base64) -- LimeZu + Pillow -------")
    lines.append("var FURNITURE_PNGS = {")

    # Sort keys for consistent output
    sorted_keys = sorted(all_sprites.keys())
    for i, name in enumerate(sorted_keys):
        b64 = all_sprites[name]
        comma = "," if i < len(sorted_keys) - 1 else ""
        lines.append(f'  {name}: "{b64}"{comma}')

    lines.append("};")
    lines.append("")

    # ── FLOOR PNGs (base64) ──
    lines.append("// -- Floor Tile PNGs (base64) per subnicho -------------------")
    lines.append("var FLOOR_PNGS = {")

    floor_keys = sorted(floor_tiles.keys())
    for i, name in enumerate(floor_keys):
        b64 = floor_tiles[name]
        comma = "," if i < len(floor_keys) - 1 else ""
        lines.append(f'  {name}: "{b64}"{comma}')

    lines.append("};")
    lines.append("")

    # ── Furniture PNG Loader (converts base64 -> string[][] via canvas) ──
    lines.append("// -- Furniture PNG Loader (async) ----------------------------")
    lines.append("var furnitureImages = {};  // name -> loaded HTMLImageElement")
    lines.append("var furnitureSpriteData = {};  // name -> string[][] (pixel grid)")
    lines.append("var floorSpriteData = {};  // subnicho -> string[][] (pixel grid)")
    lines.append("")
    lines.append("function loadFurniturePNGs(callback) {")
    lines.append("  var allKeys = Object.keys(FURNITURE_PNGS);")
    lines.append("  var floorKeys = Object.keys(FLOOR_PNGS);")
    lines.append("  var totalToLoad = allKeys.length + floorKeys.length;")
    lines.append("  var loaded = 0;")
    lines.append("  function checkDone() {")
    lines.append("    loaded++;")
    lines.append("    if (loaded >= totalToLoad && callback) callback();")
    lines.append("  }")
    lines.append("  // Load furniture sprites")
    lines.append("  for (var i = 0; i < allKeys.length; i++) {")
    lines.append("    (function(key) {")
    lines.append("      var img = new Image();")
    lines.append("      img.onload = function() {")
    lines.append("        furnitureImages[key] = img;")
    lines.append("        furnitureSpriteData[key] = imageToPixelGrid(img);")
    lines.append("        checkDone();")
    lines.append("      };")
    lines.append("      img.onerror = function() {")
    lines.append("        console.error('Failed to load furniture:', key);")
    lines.append("        checkDone();")
    lines.append("      };")
    lines.append("      img.src = FURNITURE_PNGS[key];")
    lines.append("    })(allKeys[i]);")
    lines.append("  }")
    lines.append("  // Load floor tiles")
    lines.append("  for (var j = 0; j < floorKeys.length; j++) {")
    lines.append("    (function(key) {")
    lines.append("      var img = new Image();")
    lines.append("      img.onload = function() {")
    lines.append("        floorSpriteData[key] = imageToPixelGrid(img);")
    lines.append("        checkDone();")
    lines.append("      };")
    lines.append("      img.onerror = function() {")
    lines.append("        console.error('Failed to load floor:', key);")
    lines.append("        checkDone();")
    lines.append("      };")
    lines.append("      img.src = FLOOR_PNGS[key];")
    lines.append("    })(floorKeys[j]);")
    lines.append("  }")
    lines.append("}")
    lines.append("")

    # ── imageToPixelGrid: converts loaded Image to string[][] ──
    lines.append("function imageToPixelGrid(img) {")
    lines.append("  var cv = document.createElement('canvas');")
    lines.append("  cv.width = img.width;")
    lines.append("  cv.height = img.height;")
    lines.append("  var cx = cv.getContext('2d');")
    lines.append("  cx.drawImage(img, 0, 0);")
    lines.append("  var data = cx.getImageData(0, 0, img.width, img.height).data;")
    lines.append("  var grid = [];")
    lines.append("  for (var y = 0; y < img.height; y++) {")
    lines.append("    var row = [];")
    lines.append("    for (var x = 0; x < img.width; x++) {")
    lines.append("      var idx = (y * img.width + x) * 4;")
    lines.append("      var r = data[idx], g = data[idx+1], b = data[idx+2], a = data[idx+3];")
    lines.append("      if (a < 30) {")
    lines.append("        row.push('');")
    lines.append("      } else {")
    lines.append("        var hex = '#' + ((1<<24)|(r<<16)|(g<<8)|b).toString(16).slice(1);")
    lines.append("        row.push(hex);")
    lines.append("      }")
    lines.append("    }")
    lines.append("    grid.push(row);")
    lines.append("  }")
    lines.append("  return grid;")
    lines.append("}")
    lines.append("")

    # ── getFurnitureSprite: retrieves loaded sprite as string[][] ──
    lines.append("function getFurnitureSprite(name) {")
    lines.append("  if (furnitureSpriteData[name]) return furnitureSpriteData[name];")
    lines.append("  // Fallback: return 16x16 magenta grid for debugging")
    lines.append("  var fallback = [];")
    lines.append("  for (var y = 0; y < 16; y++) {")
    lines.append("    var row = [];")
    lines.append("    for (var x = 0; x < 16; x++) {")
    lines.append("      row.push((x + y) % 2 === 0 ? '#FF00FF' : '#000000');")
    lines.append("    }")
    lines.append("    fallback.push(row);")
    lines.append("  }")
    lines.append("  return fallback;")
    lines.append("}")
    lines.append("")

    # ── getFloorSprite: retrieves floor tile as string[][] ──
    lines.append("function getFloorSprite(subnicho) {")
    lines.append("  if (floorSpriteData[subnicho]) return floorSpriteData[subnicho];")
    lines.append("  if (floorSpriteData['demonetized']) return floorSpriteData['demonetized'];")
    lines.append("  return null;  // will fall back to DEFAULT_FLOOR_SPRITE in engine")
    lines.append("}")
    lines.append("")

    # ── Now extract and keep: resolveTemplate, flipHorizontal,
    #    getCharacterSprites, getCachedSprite, getOutlineSprite,
    #    character PNG loading system ──

    # Find key sections in existing JS to preserve
    preserve_sections = extract_preserved_sections(existing_js)

    for section in preserve_sections:
        lines.append(section)

    return "\n".join(lines)


def extract_preserved_sections(js_content):
    """Extract all code from 'function resolveTemplate' to end of file,
    SKIPPING only old furniture sprite IIFE blocks that are being replaced.

    This is much simpler and more robust than trying to parse individual
    functions - just grab everything and skip known replaceable blocks.
    """

    js_lines = js_content.split('\n')

    # Find where the preserved code starts (resolveTemplate is the first function
    # after the old sprite definitions)
    start_idx = None
    for i, line in enumerate(js_lines):
        if 'function resolveTemplate' in line:
            start_idx = i
            break

    if start_idx is None:
        print("  WARNING: 'function resolveTemplate' not found in existing JS!")
        return []

    # Names of old IIFE sprite blocks to skip
    skip_iife_starts = [
        'const DESK_SQUARE_SPRITE', 'var PLANT_SPRITE', 'var BOOKSHELF_SPRITE',
        'var COOLER_SPRITE', 'var CHAIR_SPRITE', 'var PC_SPRITE',
        'var LAMP_SPRITE', 'var WHITEBOARD_SPRITE',
    ]

    result_lines = []
    i = start_idx
    while i < len(js_lines):
        stripped = js_lines[i].strip()

        # Check if this line starts an old sprite IIFE to skip
        should_skip = False
        for prefix in skip_iife_starts:
            if stripped.startswith(prefix):
                should_skip = True
                break

        if should_skip:
            # Skip entire IIFE block: track parens to find the closing });
            depth = 0
            while i < len(js_lines):
                for ch in js_lines[i]:
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                if depth <= 0 and i > start_idx:
                    i += 1
                    break
                i += 1
            continue

        # Keep this line
        result_lines.append(js_lines[i])
        i += 1

    return ['\n'.join(result_lines)]


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("LimeZu Sprite Extractor for Mission Control v3")
    print("=" * 60)

    # Verify assets exist
    for path, name in [
        (INTERIORS_PATH, "Interiors spritesheet"),
        (ROOM_BUILDER_PATH, "Room Builder spritesheet"),
    ]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found at {path}")
            return
        print(f"  [OK] {name}")

    # Load spritesheets
    print("\nLoading spritesheets...")
    interiors_img = Image.open(INTERIORS_PATH)
    room_builder_img = Image.open(ROOM_BUILDER_PATH)
    print(f"  Interiors: {interiors_img.size} ({interiors_img.mode})")
    print(f"  Room Builder: {room_builder_img.size} ({room_builder_img.mode})")

    # Extract LimeZu sprites
    print("\nExtracting LimeZu sprites...")
    limezu_sprites = extract_limezu_sprites(interiors_img, room_builder_img)
    print(f"  Extracted {len(limezu_sprites)} sprites from LimeZu")

    # Filter out empty/transparent sprites
    valid_sprites = {}
    empty_count = 0
    for name, img in limezu_sprites.items():
        if is_empty_tile(img):
            empty_count += 1
            print(f"  WARNING: {name} is empty/transparent - skipping")
        else:
            valid_sprites[name] = img

    if empty_count:
        print(f"  Skipped {empty_count} empty sprites")

    # Generate Pillow sprites for themes LimeZu doesn't cover
    print("\nGenerating themed Pillow sprites...")
    pillow_sprites = generate_pillow_sprites()
    print(f"  Generated {len(pillow_sprites)} Pillow sprites")

    # Combine all sprites
    all_sprites_images = {**valid_sprites, **pillow_sprites}

    # Scale up 2x for better detail at display size
    print("\nScaling sprites 2x for display quality...")
    scaled_sprites = {}
    for name, img in all_sprites_images.items():
        scaled = scale_sprite(img, 2)
        scaled_sprites[name] = scaled

    # Convert to base64
    print("\nConverting to base64...")
    all_base64 = {}
    total_size = 0
    for name, img in scaled_sprites.items():
        b64 = to_base64(img)
        all_base64[name] = b64
        total_size += len(b64)

    print(f"  Total base64 data: {total_size / 1024:.1f} KB ({len(all_base64)} sprites)")

    # Extract floor tiles (single 16x16 per subnicho, also scaled 2x)
    print("\nExtracting floor tiles per subnicho...")
    floor_base64 = {}
    for subnicho in ['executive', 'warroom', 'gothic', 'darklab', 'demonetized']:
        floor_img = make_floor_tile_single(room_builder_img, subnicho)
        floor_scaled = scale_sprite(floor_img, 2)
        floor_base64[subnicho] = to_base64(floor_scaled)
        print(f"  {subnicho}: {floor_img.size} -> {floor_scaled.size}")

    # Read existing JS for preserved sections
    print("\nReading existing mc_v2_part1_sprites.js for preserved sections...")
    existing_js = ""
    if os.path.exists(EXISTING_PART1):
        with open(EXISTING_PART1, 'r', encoding='utf-8') as f:
            existing_js = f.read()
        print(f"  Read {len(existing_js)} chars")
    else:
        print("  WARNING: Existing file not found - character PNG system will be missing!")

    # Build output
    print("\nBuilding output JS...")
    output_js = build_js_output(all_base64, floor_base64, existing_js)

    # Write output
    print(f"\nWriting to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output_js)

    output_size = os.path.getsize(OUTPUT_FILE)
    line_count = output_js.count('\n') + 1
    print(f"  Written: {output_size / 1024:.1f} KB, {line_count} lines")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  LimeZu sprites: {len(valid_sprites)}")
    print(f"  Pillow sprites: {len(pillow_sprites)}")
    print(f"  Floor tiles: {len(floor_base64)}")
    print(f"  Total sprites: {len(all_base64)}")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"  Size: {output_size / 1024:.1f} KB")
    print("")

    # Print sprite inventory by subnicho
    print("SPRITE INVENTORY:")
    subnicho_sprites = {
        'executive': ['desk_exec', 'chair_exec', 'pc_exec', 'bookshelf_exec', 'painting_exec',
                      'rug_exec', 'trophy', 'sofa_brown', 'plant_potted_1', 'lamp_floor_1',
                      'globe', 'aquarium', 'frame_small_1'],
        'warroom': ['desk_war', 'chair_war', 'pc_war', 'bookshelf_war', 'painting_war',
                    'arsenal', 'radar', 'radio_military', 'sandbags', 'blackboard',
                    'filing_cabinet', 'barrel', 'crate'],
        'gothic': ['desk_gothic', 'chair_gothic', 'pc_gothic', 'bookshelf_gothic', 'painting_gothic',
                   'rug_gothic', 'candelabra', 'skull_books', 'potions', 'antique_clock',
                   'curtain_closed', 'lamp_mushroom', 'plant_potted_2'],
        'darklab': ['desk_darklab', 'chair_darklab', 'pc_darklab', 'bookshelf_darklab', 'lab_table',
                    'cauldron', 'bones', 'spiderweb', 'test_tubes', 'barrel', 'crate'],
        'demonetized': ['desk_demon', 'chair_demon', 'pc_demon', 'bookshelf_demon',
                        'cardboard_box', 'desk_fan', 'coffee_mug', 'poster',
                        'vending_machine', 'plant_small_1', 'lamp_desk'],
    }

    for sub, names in subnicho_sprites.items():
        available = [n for n in names if n in all_base64]
        missing = [n for n in names if n not in all_base64]
        print(f"\n  {sub}: {len(available)}/{len(names)} sprites")
        if missing:
            print(f"    MISSING: {', '.join(missing)}")

    print("\nDone! Next: update mc_v2_part2_engine.js to use FURNITURE_PNGS")


if __name__ == '__main__':
    main()
