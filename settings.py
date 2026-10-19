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
BACKGROUND = (30, 30, 40)
TABLE = (120, 80, 40)
RIM_COLOUR = (200, 200, 210) # outer rim of a bowl seen from above
INNER_COLOUR = (150, 150, 160) # darker inner disc of a bowl (used when there is no bowl.png)
TEXT = (240, 240, 240)
GOLD = (255, 200, 40)
RED = (220, 50, 50)
GREEN = (60, 200, 90)
