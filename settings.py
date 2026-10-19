# settings.py
# Constants only. Game balance (levels, gem values) lives in the CSV files.

SCREEN = (900, 600)          # tuple: window size (width, height)
FPS = 60                     # frames per second
LIVES = 3                    # hearts at the start of a game

# TOP-DOWN view: the screen is the table top seen from above.
TABLE_Y = 320                # y of the row where the bowls rest on the table
BOWL_R = 48                  # bowl radius in pixels (bowls are circles from above)
ARC = 70                     # how far (in px) the two bowls curve apart while sliding around each other
LIFT_ASIDE = (0, -95)        # a lifted bowl is drawn slid this far from its spot (shows the gem beneath)
SHADOW_ALPHA = 70            # transparency of the soft shadow under a lifted / moving bowl

SHOW_MS = 1500               # gem visible before the round starts
COVER_MS = 600               # bowl coming down
REVEAL_MS = 1500             # bowls lifted after the choice
STREAK_FOR_BONUS = 3         # correct answers in a row needed for double points
COLLECTOR_BONUS = 100        # points for finding every gem type once

# colours as RGB tuples
# The screen background is a gradient from BACKGROUND (top) to BACKGROUND_BOTTOM
BACKGROUND = (22, 26, 42)        # night navy
BACKGROUND_BOTTOM = (11, 13, 24) # darker navy at the bottom
TABLE = (30, 104, 92)            # green felt table top
TABLE_EDGE = (20, 74, 66)        # darker border around the felt
PANEL = (32, 38, 60)             # cards and the top bar
PANEL_EDGE = (62, 72, 104)       # thin border around cards
RIM_COLOUR = (236, 232, 224)     # outer rim of a bowl (cream china)
INNER_COLOUR = (196, 188, 176)   # darker inner disc of a bowl (used when there is no bowl.png)
TEXT = (238, 241, 248)
MUTED = (146, 154, 180)          # small labels and hints
GOLD = (255, 200, 60)
RED = (240, 88, 88)
GREEN = (86, 214, 136)
