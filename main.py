# main.py
# Starts the game, runs the game loop, and draws the screens.
# state decides which screen we are on: "menu", "play", "report", "leaderboard".
# phase decides what happens inside a round (see the build doc, Section 7).

import datetime
import pygame
import data
import game
from settings import (SCREEN, FPS, TABLE_Y, BOWL_R, LIFT_ASIDE, SHADOW_ALPHA,
                      SHOW_MS, COVER_MS, REVEAL_MS, BACKGROUND, TABLE, RIM_COLOUR,
                      INNER_COLOUR, TEXT, GOLD, RED, GREEN)

# Set to True to run the 1,000-round tracking check when the game starts
DEBUG = False

# A bowl that is picked up and held to one side is shown 10% bigger
LIFT_SCALE = 1.1


def main():
    # Step 1: start pygame and open the window
    pygame.init()
    screen = pygame.display.set_mode(SCREEN)
    pygame.display.set_caption("Gem Shuffle")
    clock = pygame.time.Clock()

    # Step 2: load the fonts once, before the loop
    fonts = load_fonts()

    # Step 3: load the levels and gems from the CSV files
    levels, gems = data.load_all()
    if levels is None or gems is None:
        pygame.quit()
        return

    if DEBUG:
        game.test_tracking()

    # Step 4: the variables that the loop uses
    state = "menu"
    name = ""
    play_game = None
    round_ = None
    running = True

    while running:
        # 1. EVENTS: read what the player did
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif state == "menu":
                name, action = menu_event(event, name)
                if action == "play":
                    play_game, round_ = start_game(name, levels, gems, now)
                    state = "play"
                elif action == "leaderboard":
                    state = "leaderboard"
            elif state == "play" and round_["phase"] == "choose":
                choose_event(event, round_, play_game, len(gems), now)
            elif state in ("report", "leaderboard"):
                action = end_event(event, state)
                if action == "play":
                    play_game, round_ = start_game(name, levels, gems, now)
                    state = "play"
                elif action == "menu":
                    state = "menu"

        # 2. UPDATE: move the round or the game on
        if state == "play":
            round_, state = update_play(round_, play_game, levels, gems, now)

        # 3. DRAW: draw the screen for the current state
        if state == "menu":
            draw_menu(screen, fonts, name)
        elif state == "play":
            draw_play(screen, fonts, round_, play_game, len(levels), now)
        elif state == "report":
            draw_report(screen, fonts, play_game)
        elif state == "leaderboard":
            draw_placeholder(screen, fonts, "Leaderboard comes in step 4", "M = menu")

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


def load_fonts():
    # Font(None, size) uses pygame's built-in font, so no font file is needed
    fonts = {}
    fonts["title"] = pygame.font.Font(None, 72)
    fonts["big"] = pygame.font.Font(None, 44)
    fonts["text"] = pygame.font.Font(None, 32)
    fonts["small"] = pygame.font.Font(None, 26)
    return fonts


# ---------- menu ----------

def menu_event(event, name):
    # Returns the new name and an action ("play", "leaderboard" or None)
    if event.type != pygame.KEYDOWN:
        return name, None

    # Enter starts the game
    if event.key == pygame.K_RETURN:
        return name, "play"

    # Backspace removes the last letter
    if event.key == pygame.K_BACKSPACE:
        return name[:-1], None

    # L opens the leaderboard, but only while the name box is empty,
    # so a name can still start with the letter L
    if event.key == pygame.K_l and name == "":
        return name, "leaderboard"

    # Letters, digits and spaces are allowed, up to 12 characters
    typed = event.unicode
    if typed != "" and len(name) < 12 and (typed.isalnum() or typed == " "):
        return name + typed, None

    return name, None


def start_game(name, levels, gems, now):
    # Make a new game for this player and deal the first round.
    # An empty name becomes "Player". The game id is 0 until report.py
    # gives each game a real number in step 4.
    clean_name = name.strip()
    if clean_name == "":
        clean_name = "Player"
    play_game = game.new_game(clean_name, 0, datetime.date.today().isoformat())
    round_ = start_round(levels[0], gems, now)
    return play_game, round_


def end_event(event, state):
    # Keys on the report and leaderboard screens
    if event.type != pygame.KEYDOWN:
        return None
    if event.key == pygame.K_m:
        return "menu"
    if event.key == pygame.K_r and state == "report":
        return "play"
    return None


# ---------- round flow ----------

def start_round(level, gems, now):
    # A new round starts with the gem shown
    round_ = game.new_round(level, gems)
    set_phase(round_, "show", now)
    return round_


def set_phase(round_, phase, now):
    # Change the phase and remember when it started
    round_["phase"] = phase
    round_["phase_start"] = now


def update_play(round_, play_game, levels, gems, now):
    # Returns the round and the state ("play" or "report")
    update_round(round_, now)

    # Keep waiting until the reveal has lasted REVEAL_MS
    reveal_done = now - round_["phase_start"] >= REVEAL_MS
    if round_["phase"] != "reveal" or not reveal_done:
        return round_, "play"

    # The reveal is over: the game is over, or we start the next round
    result = check_result(play_game, levels)
    if result is None:
        round_ = start_round(levels[play_game["level_index"]], gems, now)
        return round_, "play"

    play_game["result"] = result
    return round_, "report"


def check_result(play_game, levels):
    # Out of lives means lost. Passing the last level means won.
    # levels has 10 rows, so level_index reaches 10 after the last level.
    if play_game["lives"] == 0:
        return "lost"
    if play_game["level_index"] >= len(levels):
        return "won"
    return None


def update_round(round_, now):
    # Move to the next phase when the time for this one is up
    elapsed = now - round_["phase_start"]
    if round_["phase"] == "show" and elapsed >= SHOW_MS:
        set_phase(round_, "cover", now)
    elif round_["phase"] == "cover" and elapsed >= COVER_MS:
        set_phase(round_, "shuffle", now)
    elif round_["phase"] == "shuffle":
        update_shuffle(round_, now)


def update_shuffle(round_, now):
    # All the moves are done: the player can now choose
    if round_["move_index"] >= len(round_["moves"]):
        set_phase(round_, "choose", now)
        round_["choose_start"] = now
        return

    # Has the current move finished? (t goes from 0 to 1)
    slot_a, slot_b, fake = round_["moves"][round_["move_index"]]
    t = (now - round_["phase_start"]) / round_["swap_ms"]
    if t >= 1:
        # A fake move does not really change the bowls
        if not fake:
            game.finish_swap(round_["cups_list"], slot_a, slot_b)
        round_["move_index"] += 1
        round_["phase_start"] = now


def choose_event(event, round_, play_game, gems_count, now):
    # A left click on a bowl, or the number keys 1 to 5 for a slot
    chosen = None
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        chosen = find_clicked_bowl(round_, event.pos)
    elif event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_5:
        chosen = find_bowl_in_slot(round_, event.key - pygame.K_1)

    # Nothing useful was pressed or clicked
    if chosen is None:
        return

    game.finish_round(chosen, round_, play_game, gems_count, now)
    round_["phase_start"] = now


def find_clicked_bowl(round_, pos):
    # Check each bowl's square to see if the click landed on it
    for bowl in round_["cups_list"]:
        x = round_["slots_x"][bowl["slot"]]
        if game.bowl_rect(x).collidepoint(pos):
            return bowl
    return None


def find_bowl_in_slot(round_, slot):
    # Slot 0 is the first cup, which the player sees as number 1
    for bowl in round_["cups_list"]:
        if bowl["slot"] == slot:
            return bowl
    return None


# ---------- where each bowl is drawn ----------

def bowl_pose(bowl, round_, now):
    # Returns (x, y, scale, moving) for one bowl in this frame.
    # moving is True when the bowl should get a shadow and be drawn on top.
    rest_x = round_["slots_x"][bowl["slot"]]
    lifted_x = rest_x + LIFT_ASIDE[0]
    lifted_y = TABLE_Y + LIFT_ASIDE[1]
    phase = round_["phase"]
    is_gem_bowl = bowl["id"] == round_["gem_cup"]

    # Show: the gem's bowl is held to one side, so the gem is seen
    if phase == "show" and is_gem_bowl:
        return (lifted_x, lifted_y, LIFT_SCALE, True)

    # Cover: the gem's bowl slides from the side back onto its slot
    if phase == "cover" and is_gem_bowl:
        t = min(1.0, (now - round_["phase_start"]) / COVER_MS)
        x = lifted_x + (rest_x - lifted_x) * t
        y = lifted_y + (TABLE_Y - lifted_y) * t
        return (x, y, LIFT_SCALE, True)

    # Shuffle: only the two bowls in the current move are moving
    if phase == "shuffle":
        return shuffle_pose(bowl, round_, now)

    # Reveal: the gem's bowl and the chosen bowl are held to one side
    chosen = bowl["slot"] == round_["chosen_slot"]
    if phase == "reveal" and (is_gem_bowl or chosen):
        return (lifted_x, lifted_y, LIFT_SCALE, True)

    return (rest_x, TABLE_Y, 1.0, False)


def shuffle_pose(bowl, round_, now):
    # The two bowls in the current move slide around each other
    slots_x = round_["slots_x"]
    rest = (slots_x[bowl["slot"]], TABLE_Y, 1.0, False)
    if round_["move_index"] >= len(round_["moves"]):
        return rest

    slot_a, slot_b, fake = round_["moves"][round_["move_index"]]
    t = min(1.0, (now - round_["phase_start"]) / round_["swap_ms"])

    # The bowl in slot a goes up, the bowl in slot b goes down
    if bowl["slot"] == slot_a:
        x, y = game.bowl_position(slots_x[slot_a], slots_x[slot_b], t, True, fake)
        return (x, y, 1.0, True)
    if bowl["slot"] == slot_b:
        x, y = game.bowl_position(slots_x[slot_b], slots_x[slot_a], t, False, fake)
        return (x, y, 1.0, True)
    return rest


# ---------- drawing ----------

def draw_menu(screen, fonts, name):
    screen.fill(BACKGROUND)
    draw_text(screen, fonts["title"], "Gem Shuffle", GOLD, (450, 80))

    # Name box
    draw_text(screen, fonts["text"], "Your name:", TEXT, (450, 170))
    box = pygame.Rect(300, 195, 300, 44)
    pygame.draw.rect(screen, TEXT, box, 2)
    draw_text(screen, fonts["text"], name + "_", TEXT, box.center)

    # How to play, in short lines
    lines = [
        "Watch the gem, then watch the bowls shuffle.",
        "Click the bowl that hides the gem, or press its number 1-5.",
        "A streak of 3 correct answers doubles your points.",
        "You have 3 lives. A wrong answer costs one.",
    ]
    for i in range(len(lines)):
        draw_text(screen, fonts["small"], lines[i], TEXT, (450, 300 + i * 30))

    draw_text(screen, fonts["text"], "Enter = play", GREEN, (450, 470))
    draw_text(screen, fonts["text"], "L = leaderboard (name box empty)", TEXT, (450, 510))


def draw_play(screen, fonts, round_, play_game, total_levels, now):
    # Drawing order: table, slot numbers, gem, shadows, resting bowls,
    # moving bowls, then the HUD on top
    screen.fill(TABLE)
    draw_slot_numbers(screen, fonts, round_)
    draw_bowls(screen, round_, now)
    draw_hud(screen, fonts, round_, play_game, total_levels)


def draw_slot_numbers(screen, fonts, round_):
    # Numbers under each resting slot, to match the number keys
    for i in range(len(round_["slots_x"])):
        x = round_["slots_x"][i]
        draw_text(screen, fonts["small"], str(i + 1), TEXT, (int(x), TABLE_Y + BOWL_R + 18))


def draw_bowls(screen, round_, now):
    # Work out where every bowl is this frame
    poses = []
    for bowl in round_["cups_list"]:
        poses.append(bowl_pose(bowl, round_, now))

    # The gem lies flat on the table under its bowl.
    # It is drawn before the bowls, so a bowl on top hides it.
    if round_["phase"] in ("show", "cover", "reveal"):
        gem_bowl = find_gem_bowl(round_)
        draw_gem(screen, round_["slots_x"][gem_bowl["slot"]], TABLE_Y)

    # Shadows for the moving bowls go under all the bowls
    for pose in poses:
        if pose[3]:
            draw_shadow(screen, int(pose[0]), int(pose[1]))

    # Resting bowls, then the moving bowls on top
    for pose in poses:
        if not pose[3]:
            draw_bowl(screen, pose[0], pose[1], pose[2])
    for pose in poses:
        if pose[3]:
            draw_bowl(screen, pose[0], pose[1], pose[2])


def find_gem_bowl(round_):
    # The bowl that hides the gem, found by its id
    for bowl in round_["cups_list"]:
        if bowl["id"] == round_["gem_cup"]:
            return bowl
    return None


def draw_bowl(screen, x, y, scale):
    # A bowl seen from above: a light outer rim and a darker inner disc
    centre = (int(x), int(y))
    pygame.draw.circle(screen, RIM_COLOUR, centre, int(BOWL_R * scale))
    pygame.draw.circle(screen, INNER_COLOUR, centre, int((BOWL_R - 10) * scale))


def draw_shadow(screen, x, y):
    # A soft dark circle, offset 6 px right and down, drawn under the bowl.
    # Black is set as the see-through colour, and the whole thing is
    # made partly see-through with set_alpha.
    size = BOWL_R * 2
    shadow = pygame.Surface((size, size))
    shadow.set_colorkey((0, 0, 0))
    pygame.draw.circle(shadow, (40, 40, 40), (BOWL_R, BOWL_R), BOWL_R)
    shadow.set_alpha(SHADOW_ALPHA)
    screen.blit(shadow, (x + 6 - BOWL_R, y + 6 - BOWL_R))


def draw_gem(screen, x, y):
    # A small flat diamond shape lying on the table
    points = [(x, y - 14), (x + 12, y), (x, y + 14), (x - 12, y)]
    pygame.draw.polygon(screen, GOLD, points)


def draw_hud(screen, fonts, round_, play_game, total_levels):
    # Top line: level, streak and score
    top = "Level {} / {}     Streak {}     Score {}".format(
        round_["level"], total_levels, play_game["streak"], play_game["score"])
    draw_text(screen, fonts["text"], top, TEXT, (450, 30))

    # Hearts: one red circle per life left
    for i in range(play_game["lives"]):
        pygame.draw.circle(screen, RED, (420 + i * 30, 70), 10)

    # The gem's name is shown during the show and reveal phases
    if round_["phase"] in ("show", "cover", "reveal"):
        draw_text(screen, fonts["text"], "Gem: " + round_["gem"]["gem"], GOLD, (450, 110))

    # Phase text at the bottom of the screen
    draw_phase_text(screen, fonts, round_)


def draw_phase_text(screen, fonts, round_):
    phase = round_["phase"]
    if phase == "show":
        draw_text(screen, fonts["big"], "Watch the gem...", TEXT, (450, 530))
    elif phase == "cover":
        draw_text(screen, fonts["big"], "Covering the gem...", TEXT, (450, 530))
    elif phase == "shuffle":
        done = min(round_["move_index"] + 1, len(round_["moves"]))
        text = "Shuffling {} / {}".format(done, len(round_["moves"]))
        draw_text(screen, fonts["big"], text, TEXT, (450, 530))
    elif phase == "choose":
        draw_text(screen, fonts["big"], "Pick a bowl!", GOLD, (450, 530))
    elif phase == "reveal":
        if round_["correct"] == 1:
            text = "Correct! +{}".format(round_["points"])
            draw_text(screen, fonts["big"], text, GREEN, (450, 530))
        else:
            draw_text(screen, fonts["big"], "Wrong!", RED, (450, 530))


def draw_report(screen, fonts, play_game):
    # Placeholder until report.py is written in step 4
    lines = [
        "Game over: {}".format(play_game["result"]),
        "Score: {}".format(play_game["score"]),
        "The Focus Report comes in step 4",
    ]
    draw_placeholder(screen, fonts, lines, "R = play again     M = menu")


def draw_placeholder(screen, fonts, lines, footer):
    # Shows a few centred lines and a footer. Used for screens not built yet.
    if isinstance(lines, str):
        lines = [lines]
    screen.fill(BACKGROUND)
    for i in range(len(lines)):
        draw_text(screen, fonts["text"], lines[i], TEXT, (450, 220 + i * 40))
    draw_text(screen, fonts["text"], footer, GREEN, (450, 500))


def draw_text(screen, font, text, colour, centre):
    # Draw text centred on the given point
    surface = font.render(text, True, colour)
    screen.blit(surface, surface.get_rect(center=centre))


if __name__ == "__main__":
    main()
