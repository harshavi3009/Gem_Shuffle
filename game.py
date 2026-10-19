# game.py
# Bowls, swaps, animation maths, clicks and scoring.
# Nothing in this file draws to the screen, except bowl_rect which only
# makes a rectangle for click checks.

import math
import numpy as np
import pygame
import data
from settings import ARC, TABLE_Y, BOWL_R, STREAK_FOR_BONUS, COLLECTOR_BONUS


def new_game(player, game_id, date):
    # A game is one dictionary that holds the whole run of a player
    game = {
        "id": game_id,
        "player": player,
        "date": date,
        "score": 0,
        "lives": 3,
        "streak": 0,
        "best_streak": 0,
        "level_index": 0,
        "gems_won": set(),       # a set: no gem name can be in it twice
        "bonus_given": False,
        "rounds": [],
        "result": None,
    }
    return game


def new_round(level, gems):
    # Step 1: make one bowl for each cup. The id never changes,
    # the slot changes every time bowls swap.
    cups = int(level["cups"])
    cups_list = []
    for i in range(cups):
        cups_list.append({"id": i, "slot": i})

    # Step 2: work out the x position of each slot, spread evenly
    slots_x = list(np.linspace(150, 750, cups))

    # Step 3: pick the hidden gem. Rarer gems have a smaller weight,
    # so they are picked less often.
    weights = []
    for gem in gems:
        weights.append(gem["rarity_weight"])
    weights = np.array(weights)
    gem_index = np.random.choice(len(gems), p=weights / weights.sum())

    # Step 4: pick which cup hides the gem (any cup, all equally likely)
    gem_cup = int(np.random.randint(0, cups))

    # Step 5: make the list of swaps for this round
    moves = make_swaps(level)

    # Step 6: put everything into one dictionary for this round
    round_ = {
        "level": int(level["level"]),
        "cups": cups,
        "swaps": int(level["swaps"]),
        "fakes": int(level["fakes"]),
        "swap_ms": int(level["swap_ms"]),
        "cups_list": cups_list,
        "slots_x": slots_x,
        "gem": gems[gem_index],
        "gem_cup": gem_cup,
        "start_slot": gem_cup,
        "moves": moves,
        "move_index": 0,
        "phase": "show",
        "phase_start": 0,
        "choose_start": 0,
        "chosen_slot": None,
        "answer_slot": None,
        "correct": None,
        "reaction_s": None,
        "points": 0,
        "second": 0,
    }
    return round_


def make_swaps(level):
    cups = int(level["cups"])
    moves = []

    # Step 1: real swaps. Pick 2 different cups at random, no repeats.
    for n in range(int(level["swaps"])):
        pair = np.random.choice(cups, 2, replace=False)
        moves.append((int(pair[0]), int(pair[1]), False))

    # Step 2: fake swaps. They are shown on screen, but the bowls do
    # not really change place. Each one goes in at a random point.
    for n in range(int(level["fakes"])):
        pair = np.random.choice(cups, 2, replace=False)
        position = np.random.randint(0, len(moves) + 1)
        moves.insert(int(position), (int(pair[0]), int(pair[1]), True))

    return moves


def bowl_position(start_x, end_x, t, goes_up, fake):
    # t goes from 0 (start of the move) to 1 (end of the move)

    # Step 1: sideways movement. A fake move goes halfway and comes back.
    if fake:
        x = start_x + (end_x - start_x) * 0.5 * math.sin(math.pi * t)
    else:
        x = start_x + (end_x - start_x) * t

    # Step 2: the curve. It is 0 at the start and end, and ARC in the middle.
    curve = ARC * math.sin(math.pi * t)

    # Step 3: one bowl bends up the screen, the other bends down
    if goes_up:
        y = TABLE_Y - curve
    else:
        y = TABLE_Y + curve

    return (x, y)


def finish_swap(cups_list, a, b):
    # Find the bowl in slot a and the bowl in slot b
    bowl_a = None
    bowl_b = None
    for bowl in cups_list:
        if bowl["slot"] == a:
            bowl_a = bowl
        if bowl["slot"] == b:
            bowl_b = bowl

    # Swap their slot numbers. The bowl ids stay the same.
    bowl_a["slot"] = b
    bowl_b["slot"] = a


def answer_slot(round_):
    # Find the slot where the bowl with the gem is standing now
    for bowl in round_["cups_list"]:
        if bowl["id"] == round_["gem_cup"]:
            return bowl["slot"]
    return None


def finish_round(chosen_bowl, round_, game, gems_count, now):
    # Step 1: write down what the player chose and the right answer
    round_["chosen_slot"] = chosen_bowl["slot"]
    round_["answer_slot"] = answer_slot(round_)

    # Step 2: reaction time in seconds, to 2 decimal places
    round_["reaction_s"] = round((now - round_["choose_start"]) / 1000.0, 2)

    # Step 3: right or wrong
    if round_["chosen_slot"] == round_["answer_slot"]:
        round_["correct"] = 1
        finish_correct(round_, game, gems_count)
    else:
        round_["correct"] = 0
        finish_wrong(game)

    # Step 4: save the round and move to the reveal screen
    game["rounds"].append(round_)
    round_["phase"] = "reveal"


def finish_correct(round_, game, gems_count):
    # Step 1: a correct answer adds one to the streak
    game["streak"] += 1
    game["best_streak"] = max(game["best_streak"], game["streak"])

    # Step 2: points = gem value x level number
    points = int(round_["gem"]["value"] * round_["level"])

    # Step 3: double the points when the streak is long enough
    if game["streak"] >= STREAK_FOR_BONUS:
        points = points * 2
    round_["points"] = points
    game["score"] += points

    # Step 4: remember this gem name. Sets never store a name twice.
    game["gems_won"].add(round_["gem"]["gem"])

    # Step 5: give the collector bonus only once, when every gem is found
    if len(game["gems_won"]) == gems_count and not game["bonus_given"]:
        game["score"] += COLLECTOR_BONUS
        game["bonus_given"] = True

    # Step 6: go on to the next level
    game["level_index"] += 1


def finish_wrong(game):
    # A wrong answer costs a life and breaks the streak.
    # The level stays the same, so the player tries the same level again.
    game["lives"] -= 1
    game["streak"] = 0


def bowl_rect(x):
    # A square around the bowl's circle, used to check mouse clicks
    return pygame.Rect(x - BOWL_R, TABLE_Y - BOWL_R, 2 * BOWL_R, 2 * BOWL_R)


def test_tracking():
    # Self-check: play 1,000 random rounds without drawing.
    # Way 1 is the normal method: follow the bowl ids through the moves.
    # Way 2 keeps a list called order, where order[slot] = bowl id.
    # Both must end up with the gem in the same slot.
    levels, gems = data.load_all()
    for n in range(1000):
        # Pick a random level, then make a round
        level = levels[np.random.randint(0, len(levels))]
        round_ = new_round(level, gems)

        # Way 2 starts with the bowl ids in slot order
        order = []
        for bowl in round_["cups_list"]:
            order.append(bowl["id"])

        # Do every move. Only real moves change the bowls.
        for move in round_["moves"]:
            slot_a, slot_b, fake = move
            if not fake:
                finish_swap(round_["cups_list"], slot_a, slot_b)
                temp = order[slot_a]
                order[slot_a] = order[slot_b]
                order[slot_b] = temp

        # Both ways must agree on the final slot of the gem
        way_1 = answer_slot(round_)
        way_2 = order.index(round_["gem_cup"])
        assert way_1 == way_2, "Round {} disagrees: {} vs {}".format(n, way_1, way_2)

    print("test_tracking passed: 1000 rounds agree")
