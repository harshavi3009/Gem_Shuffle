# main.py
# Starts the game, runs the game loop, and draws the screens.
# state decides which screen we are on: "menu", "play", "report", "leaderboard".
# phase decides what happens inside a round (see the build doc, Section 7).

import datetime
import pygame
import data
import game
import report
import ui
from settings import (SCREEN, FPS, TABLE_Y, BOWL_R, LIFT_ASIDE, SHADOW_ALPHA, LIVES,
                      SHOW_MS, COVER_MS, REVEAL_MS, BACKGROUND, TABLE, TABLE_EDGE,
                      PANEL, PANEL_EDGE, RIM_COLOUR, INNER_COLOUR, TEXT, MUTED,
                      GOLD, RED, GREEN)

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

    # Step 2: load the fonts and the background once, before the loop
    fonts = load_fonts()
    background = ui.make_background()

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
    board_rows = []
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
                    board_rows = report.leaderboard_rows()
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

        # 3. DRAW: the background first, then the screen for the current state
        screen.blit(background, (0, 0))
        if state == "menu":
            draw_menu(screen, fonts, name, now)
        elif state == "play":
            draw_play(screen, fonts, round_, play_game, len(levels), now)
        elif state == "report":
            report.draw_focus(screen, fonts, play_game)
        elif state == "leaderboard":
            report.draw_leaderboard(screen, fonts, board_rows)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


def load_fonts():
    # Font(None, size) uses pygame's built-in font, so no font file is needed
    fonts = {}
    fonts["title"] = pygame.font.Font(None, 76)
    fonts["big"] = pygame.font.Font(None, 46)
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
    # gives each game a real number when it is saved.
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

    # The game is over: save it, and work out the Focus Report numbers
    play_game["result"] = result
    report.save_game(play_game)
    play_game["focus"] = report.focus_report(play_game, gems)
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

def draw_menu(screen, fonts, name, now):
    # The title, then one card with the name box, the rules and the buttons
    ui.draw_text(screen, fonts["title"], "Gem Shuffle", GOLD, (450, 70))
    ui.draw_text(screen, fonts["small"], "Find the gem under the bowls", MUTED, (450, 115))
    ui.draw_panel(screen, pygame.Rect(150, 150, 600, 380))

    # Name box, with a blinking caret after the name
    ui.draw_text_left(screen, fonts["small"], "YOUR NAME", MUTED, (190, 178))
    box = pygame.Rect(190, 205, 520, 50)
    pygame.draw.rect(screen, BACKGROUND, box, border_radius=10)
    pygame.draw.rect(screen, GOLD, box, 2, border_radius=10)
    caret = "|" if (now // 500) % 2 == 0 else " "
    ui.draw_text_left(screen, fonts["text"], name + caret, TEXT, (box.x + 16, box.y + 13))

    # How to play, in short lines
    lines = [
        "Watch the gem, then watch the bowls shuffle.",
        "Click the bowl that hides the gem, or press 1 to 5.",
        "3 correct answers in a row doubles your points.",
        "You have 3 lives. A wrong answer costs one.",
    ]
    for i in range(len(lines)):
        ui.draw_text_left(screen, fonts["small"], lines[i], TEXT, (190, 282 + i * 30))

    # Buttons, and a hint about the L key
    ui.draw_pill(screen, fonts["text"], "Enter  Play", BACKGROUND, GREEN, (330, 462))
    ui.draw_pill(screen, fonts["text"], "L  Leaderboard", TEXT, PANEL_EDGE, (600, 462))
    ui.draw_text(screen, fonts["small"], "The L key works only while the name box is empty.", MUTED, (450, 508))


def draw_play(screen, fonts, round_, play_game, total_levels, now):
    # Drawing order: the top bar, the table, slot numbers, the gem,
    # shadows, resting bowls, moving bowls, the rings, and the phase text
    draw_hud(screen, fonts, round_, play_game, total_levels)
    ui.draw_panel(screen, pygame.Rect(40, 150, 820, 330), TABLE, TABLE_EDGE)
    draw_slot_numbers(screen, fonts, round_)
    draw_bowls(screen, round_, now)
    draw_phase_text(screen, fonts, round_)


def draw_slot_numbers(screen, fonts, round_):
    # Numbers under each resting slot, to match the number keys
    for i in range(len(round_["slots_x"])):
        x = round_["slots_x"][i]
        ui.draw_text(screen, fonts["small"], str(i + 1), TEXT, (int(x), TABLE_Y + BOWL_R + 18))


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

    draw_rings(screen, round_, poses)


def draw_rings(screen, round_, poses):
    # Coloured rings show what the player can click, and what was right.
    # They are drawn last, so they sit on top of the bowls.
    phase = round_["phase"]
    for i in range(len(poses)):
        bowl = round_["cups_list"][i]
        centre = (int(poses[i][0]), int(poses[i][1]))

        # Choose phase: a gold ring under the mouse shows the bowl you will pick
        if phase == "choose":
            rest_x = round_["slots_x"][bowl["slot"]]
            if game.bowl_rect(rest_x).collidepoint(pygame.mouse.get_pos()):
                pygame.draw.circle(screen, GOLD, centre, BOWL_R + 8, 3)

        # Reveal phase: green for the right bowl, red for a wrong pick
        if phase == "reveal" and bowl["slot"] == round_["answer_slot"]:
            pygame.draw.circle(screen, GREEN, centre, BOWL_R + 8, 4)
        if phase == "reveal" and round_["correct"] == 0 and bowl["slot"] == round_["chosen_slot"]:
            pygame.draw.circle(screen, RED, centre, BOWL_R + 8, 4)


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
    pygame.draw.circle(shadow, (20, 50, 45), (BOWL_R, BOWL_R), BOWL_R)
    shadow.set_alpha(SHADOW_ALPHA)
    screen.blit(shadow, (x + 6 - BOWL_R, y + 6 - BOWL_R))


def draw_gem(screen, x, y):
    # A small flat diamond shape lying on the table
    points = [(x, y - 14), (x + 12, y), (x, y + 14), (x - 12, y)]
    pygame.draw.polygon(screen, GOLD, points)


def draw_hud(screen, fonts, round_, play_game, total_levels):
    # The top bar: level, streak, score and lives, each with a small label
    ui.draw_panel(screen, pygame.Rect(40, 14, 820, 70))
    draw_stat(screen, fonts, "LEVEL", "{} / {}".format(round_["level"], total_levels), 170)
    draw_stat(screen, fonts, "STREAK", str(play_game["streak"]), 390)
    draw_stat(screen, fonts, "SCORE", str(play_game["score"]), 610)
    draw_lives(screen, fonts, play_game["lives"], 770)

    # The gem's name shows during show, cover and reveal. Otherwise it is hidden.
    if round_["phase"] in ("show", "cover", "reveal"):
        ui.draw_pill(screen, fonts["text"], "Gem: " + round_["gem"]["gem"], GOLD, PANEL, (450, 112))
    else:
        ui.draw_pill(screen, fonts["text"], "Gem hidden", MUTED, PANEL, (450, 112))


def draw_stat(screen, fonts, label, value, centre_x):
    # A small label above a big value
    ui.draw_text(screen, fonts["small"], label, MUTED, (centre_x, 30))
    ui.draw_text(screen, fonts["big"], value, TEXT, (centre_x, 58))


def draw_lives(screen, fonts, lives, centre_x):
    # One circle for each life: filled while you still have it, empty once lost
    ui.draw_text(screen, fonts["small"], "LIVES", MUTED, (centre_x, 30))
    for i in range(LIVES):
        x = centre_x - 22 + i * 22
        if i < lives:
            pygame.draw.circle(screen, RED, (x, 58), 8)
        else:
            pygame.draw.circle(screen, PANEL_EDGE, (x, 58), 8, 2)


def draw_phase_text(screen, fonts, round_):
    # The message pill at the bottom, coloured to match the phase
    phase = round_["phase"]
    if phase == "show":
        ui.draw_pill(screen, fonts["big"], "Watch the gem...", TEXT, PANEL, (450, 530))
    elif phase == "cover":
        ui.draw_pill(screen, fonts["big"], "Covering the gem...", TEXT, PANEL, (450, 530))
    elif phase == "shuffle":
        draw_shuffle_progress(screen, fonts, round_)
    elif phase == "choose":
        ui.draw_pill(screen, fonts["big"], "Pick a bowl!", BACKGROUND, GOLD, (450, 530))
        ui.draw_text(screen, fonts["small"], "Click a bowl, or press its number 1 to 5", MUTED, (450, 566))
    elif phase == "reveal":
        draw_reveal_text(screen, fonts, round_)


def draw_shuffle_progress(screen, fonts, round_):
    # The text says how many moves are done, and a bar fills up as they go
    done = min(round_["move_index"] + 1, len(round_["moves"]))
    total = len(round_["moves"])
    ui.draw_pill(screen, fonts["big"], "Shuffling {} / {}".format(done, total), TEXT, PANEL, (450, 530))
    bar = pygame.Rect(300, 562, 300, 8)
    pygame.draw.rect(screen, PANEL_EDGE, bar, border_radius=4)
    filled = int(300 * round_["move_index"] / total)
    pygame.draw.rect(screen, GOLD, pygame.Rect(300, 562, filled, 8), border_radius=4)


def draw_reveal_text(screen, fonts, round_):
    # Green for a right answer, red for a wrong one
    if round_["correct"] == 1:
        text = "Correct! +{}".format(round_["points"])
        ui.draw_pill(screen, fonts["big"], text, BACKGROUND, GREEN, (450, 530))
    else:
        ui.draw_pill(screen, fonts["big"], "Wrong!", TEXT, RED, (450, 530))


if __name__ == "__main__":
    main()
