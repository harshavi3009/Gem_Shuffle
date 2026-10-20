# report.py
# Saves each game to CSV files, works out the Focus Report numbers,
# and draws the Focus Report and the leaderboard.

import os
import numpy as np
import pandas as pd
import pygame
import ui
from settings import TEXT, MUTED, GOLD, GREEN, PANEL_EDGE, BACKGROUND, BAR_COLOURS, SILVER, BRONZE

ROUNDS_PATH = os.path.join("data", "rounds.csv")
GAMES_PATH = os.path.join("data", "games.csv")
ROUNDS_HEADER = "game_id,player,date,level,cups,swaps,fakes,swap_ms,gem,start_slot,answer_slot,chosen_slot,correct,reaction_s,points\n"
GAMES_HEADER = "game_id,player,date,score,level_reached,rounds,correct,best_streak,avg_reaction_s,gems_won,result\n"


# ---------- saving ----------

def save_game(game):
    # Step 1: give this game a number: one more than the games already saved
    game["id"] = next_game_id()

    # Step 2: write one line per round, then one line for the whole game
    save_rounds(game)
    save_game_row(game)


def next_game_id():
    # If there is no games file yet, this is the first game
    if not os.path.exists(GAMES_PATH):
        return 1
    games = pd.read_csv(GAMES_PATH)
    return len(games) + 1


def save_rounds(game):
    # The header line is only written the first time, when the file is new
    write_header = not os.path.exists(ROUNDS_PATH)
    player = game["player"].replace(",", "")

    # "a" means append: new lines go to the end, old lines stay
    with open(ROUNDS_PATH, "a") as f:
        if write_header:
            f.write(ROUNDS_HEADER)
        for round_ in game["rounds"]:
            f.write(round_line(game["id"], player, game["date"], round_))


def round_line(game_id, player, date, round_):
    # Put one round's numbers into one comma-separated line
    return "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
        game_id, player, date,
        round_["level"], round_["cups"], round_["swaps"], round_["fakes"], round_["swap_ms"],
        round_["gem"]["gem"], round_["start_slot"], round_["answer_slot"], round_["chosen_slot"],
        round_["correct"], round_["reaction_s"], round_["points"])


def save_game_row(game):
    write_header = not os.path.exists(GAMES_PATH)
    player = game["player"].replace(",", "")

    # Gem names are joined with ";" because a comma would split the column
    gems_text = ";".join(sorted(game["gems_won"]))

    # The number of correct answers, and the average reaction time
    correct = count_correct(game["rounds"])
    avg_reaction = average_reaction(game["rounds"])

    line = "{},{},{},{},{},{},{},{},{},{},{}\n".format(
        game["id"], player, game["date"], game["score"], level_reached(game),
        len(game["rounds"]), correct, game["best_streak"], avg_reaction,
        gems_text, game["result"])

    with open(GAMES_PATH, "a") as f:
        if write_header:
            f.write(GAMES_HEADER)
        f.write(line)


def level_reached(game):
    # If the player won, they reached the last level (level_index is 10).
    # If they lost, they were still on the level after level_index.
    if game["result"] == "won":
        return game["level_index"]
    return game["level_index"] + 1


def count_correct(rounds):
    total = 0
    for round_ in rounds:
        total += round_["correct"]
    return total


def average_reaction(rounds):
    # A game with no rounds has an average of 0
    if len(rounds) == 0:
        return 0
    total = 0.0
    for round_ in rounds:
        total += round_["reaction_s"]
    return round(total / len(rounds), 2)


# ---------- the Focus Report numbers ----------

def focus_report(game, gems_list):
    # Returns a dictionary of numbers for the report screen
    stats = {}
    stats["better_than"] = better_than(game["score"])
    stats["gems_collected"] = len(game["gems_won"])
    stats["gems_total"] = len(gems_list)
    stats["still_to_find"] = still_to_find(game, gems_list)

    # A game with no rounds has no answers to measure
    if len(game["rounds"]) == 0:
        stats["accuracy"] = 0
        stats["avg_reaction"] = 0
        stats["slow_decision"] = 0
        stats["favourite_slot"] = None
        stats["favourite_share"] = 0
        stats["acc_by_cups"] = pd.Series(dtype=float)
        return stats

    rounds = pd.DataFrame(game["rounds"])
    reaction_s = np.array(rounds["reaction_s"])
    stats["accuracy"] = round(rounds["correct"].mean() * 100)
    stats["avg_reaction"] = round(reaction_s.mean(), 2)
    stats["slow_decision"] = round(np.percentile(reaction_s, 90), 2)

    # The slot the player picked most often
    counts = rounds.groupby("chosen_slot").size()
    stats["favourite_slot"] = int(counts.idxmax())
    stats["favourite_share"] = round(counts.max() / len(rounds) * 100)

    # Accuracy for each number of bowls, all players together
    stats["acc_by_cups"] = acc_by_cups()
    return stats


def better_than(score):
    # The percentage of saved games with a lower score than this one
    if not os.path.exists(GAMES_PATH):
        return 0
    scores = np.array(pd.read_csv(GAMES_PATH)["score"])
    if len(scores) == 0:
        return 0
    return round((scores < score).mean() * 100)


def still_to_find(game, gems_list):
    # All gem names, minus the ones the player has already found
    all_names = set()
    for gem in gems_list:
        all_names.add(gem["gem"])
    return all_names - game["gems_won"]


def acc_by_cups():
    # Read every saved round from every player, then average by bowl count
    if not os.path.exists(ROUNDS_PATH):
        return pd.Series(dtype=float)
    rounds = pd.read_csv(ROUNDS_PATH)
    return rounds.groupby("cups")["correct"].mean() * 100


def leaderboard_rows():
    # The top 5 games by score, best first
    if not os.path.exists(GAMES_PATH):
        return []
    games = pd.read_csv(GAMES_PATH)
    top = games.sort_values("score", ascending=False).head(5)
    return top.to_dict("records")


# ---------- drawing ----------
# The background is already on the screen when these run (main.py draws it first)

def draw_focus(screen, fonts, play_game):
    # Two cards: the statistics on the left, the bar chart on the right
    stats = play_game["focus"]
    ui.draw_text_left(screen, fonts["big"], "Focus Report", GOLD, (40, 30))
    subtitle = "{}   -   score {}   -   {}".format(play_game["player"], play_game["score"], play_game["result"])
    ui.draw_text_left(screen, fonts["small"], subtitle, MUTED, (42, 72))

    ui.draw_panel(screen, pygame.Rect(40, 110, 430, 380))
    draw_stat_rows(screen, fonts, stats)
    ui.draw_panel(screen, pygame.Rect(490, 110, 370, 380))
    draw_bars(screen, fonts, stats["acc_by_cups"])

    ui.draw_pill(screen, fonts["text"], "R  Play again", BACKGROUND, GREEN, (320, 530))
    ui.draw_pill(screen, fonts["text"], "M  Menu", TEXT, PANEL_EDGE, (580, 530))


def draw_stat_rows(screen, fonts, stats):
    # Each row: a label on the left, the value on the right
    favourite = "-"
    if stats["favourite_slot"] is not None:
        favourite = str(stats["favourite_slot"] + 1)
    rows = [
        ("Better than", "{}% of players".format(stats["better_than"])),
        ("Accuracy", "{}%".format(stats["accuracy"])),
        ("Average reaction", "{} s".format(stats["avg_reaction"])),
        ("Slowest 10% of decisions", "{} s".format(stats["slow_decision"])),
        ("Favourite bowl", "number {} ({}%)".format(favourite, stats["favourite_share"])),
        ("Gems found", "{} of {}".format(stats["gems_collected"], stats["gems_total"])),
    ]
    for i in range(len(rows)):
        y = 135 + i * 46
        ui.draw_text_left(screen, fonts["small"], rows[i][0], MUTED, (62, y))
        ui.draw_text_right(screen, fonts["text"], rows[i][1], TEXT, (448, y - 2))

    # Still to find: the gems not found yet, in alphabetical order
    still = ", ".join(sorted(stats["still_to_find"]))
    if still != "":
        ui.draw_text_left(screen, fonts["small"], "Still to find", MUTED, (62, 415))
        ui.draw_text_left(screen, fonts["small"], still, TEXT, (62, 437))


def draw_bars(screen, fonts, acc):
    # acc is a table: the bowl count is the label, the accuracy % is the value.
    # The longest bar is 130 pixels; the others are scaled to it.
    ui.draw_text_left(screen, fonts["text"], "Accuracy by bowls", TEXT, (512, 130))
    ui.draw_text_left(screen, fonts["small"], "all players", MUTED, (512, 160))
    if len(acc) == 0:
        ui.draw_text_left(screen, fonts["small"], "No rounds saved yet", MUTED, (512, 200))
        return
    biggest = acc.max()
    y = 200
    for i, (bowls, value) in enumerate(acc.items()):
        width = 0
        if biggest > 0:
            width = int(130 * value / biggest)
        # Each bar gets the next colour in the list, wrapping round if there are more bars
        bar_colour = BAR_COLOURS[i % len(BAR_COLOURS)]
        if width > 0:
            pygame.draw.rect(screen, bar_colour, (512, y, width, 24), border_radius=6)
        label = "{} bowls  {}%".format(int(bowls), int(round(value)))
        ui.draw_text_left(screen, fonts["small"], label, TEXT, (512 + 130 + 12, y + 3))
        y += 46


def draw_leaderboard(screen, fonts, rows):
    # One card with a heading row, then the top 5 games
    ui.draw_text_left(screen, fonts["big"], "Leaderboard", GOLD, (40, 30))
    ui.draw_text_left(screen, fonts["small"], "Top 5 games by score", MUTED, (42, 72))
    ui.draw_panel(screen, pygame.Rect(40, 110, 820, 380))

    headings = [("Player", 70), ("Score", 380), ("Level", 540), ("Result", 700)]
    for label, x in headings:
        ui.draw_text_left(screen, fonts["small"], label, MUTED, (x, 132))

    for i in range(len(rows)):
        row = rows[i]
        y = 170 + i * 56
        # Gold, silver and bronze for the top three places
        place_colours = [GOLD, SILVER, BRONZE]
        colour = TEXT
        if i < len(place_colours):
            colour = place_colours[i]
        ui.draw_text_left(screen, fonts["text"], str(row["player"]), colour, (70, y))
        ui.draw_text_left(screen, fonts["text"], str(row["score"]), colour, (380, y))
        ui.draw_text_left(screen, fonts["text"], str(row["level_reached"]), colour, (540, y))
        ui.draw_text_left(screen, fonts["text"], str(row["result"]), colour, (700, y))
    if len(rows) == 0:
        ui.draw_text_left(screen, fonts["text"], "No games saved yet", MUTED, (70, 170))

    ui.draw_pill(screen, fonts["text"], "M  Menu", TEXT, PANEL_EDGE, (450, 530))
