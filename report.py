# report.py
# Saves each game to CSV files, works out the Focus Report numbers,
# and draws the Focus Report and the leaderboard.

import os
import numpy as np
import pandas as pd
import pygame
from settings import BACKGROUND, TEXT, GOLD, GREEN

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

def draw_focus(screen, fonts, play_game):
    # The Focus Report screen: text rows, then the bar chart
    stats = play_game["focus"]
    screen.fill(BACKGROUND)
    draw_line(screen, fonts["big"], "Focus Report", GOLD, (40, 30))

    # Text rows, one for each statistic
    rows = [
        "Player: {}     Score: {}     Result: {}".format(
            play_game["player"], play_game["score"], play_game["result"]),
        "You scored higher than {}% of all players".format(stats["better_than"]),
        "Accuracy: {}%".format(stats["accuracy"]),
        "Average reaction: {} s     Slowest 10% of decisions: {} s".format(
            stats["avg_reaction"], stats["slow_decision"]),
        "Favourite bowl: number {} ({}% of your picks)".format(
            stats["favourite_slot"] + 1 if stats["favourite_slot"] is not None else "-",
            stats["favourite_share"]),
        "Gems found: {} of {}".format(stats["gems_collected"], stats["gems_total"]),
    ]
    for i in range(len(rows)):
        draw_line(screen, fonts["text"], rows[i], TEXT, (40, 80 + i * 34))

    # Still to find: names that are not found yet, in alphabetical order
    still = ", ".join(sorted(stats["still_to_find"]))
    if still != "":
        draw_line(screen, fonts["small"], "Still to find: " + still, TEXT, (40, 290))

    draw_bars(screen, fonts, stats["acc_by_cups"])
    draw_line(screen, fonts["text"], "R = play again     M = menu", GREEN, (40, 570))


def draw_bars(screen, fonts, acc):
    # acc is a table: the bowl count is the label, the accuracy % is the value.
    # The longest bar is 130 pixels; the others are scaled to it.
    draw_line(screen, fonts["text"], "Accuracy by number of bowls (all players)", TEXT, (40, 330))
    if len(acc) == 0:
        return
    biggest = acc.max()
    y = 370
    for bowls, value in acc.items():
        width = 0
        if biggest > 0:
            width = int(130 * value / biggest)
        pygame.draw.rect(screen, GREEN, (40, y, width, 22))
        label = "{} bowls {}%".format(int(bowls), int(round(value)))
        draw_line(screen, fonts["small"], label, TEXT, (40 + 130 + 12, y))
        y += 34


def draw_leaderboard(screen, fonts, rows):
    # The top 5 games, with a heading row
    screen.fill(BACKGROUND)
    draw_line(screen, fonts["big"], "Leaderboard (top 5)", GOLD, (40, 30))
    draw_line(screen, fonts["text"], "Player", GOLD, (40, 90))
    draw_line(screen, fonts["text"], "Score", GOLD, (300, 90))
    draw_line(screen, fonts["text"], "Level", GOLD, (450, 90))
    draw_line(screen, fonts["text"], "Result", GOLD, (600, 90))
    for i in range(len(rows)):
        row = rows[i]
        y = 130 + i * 40
        draw_line(screen, fonts["text"], str(row["player"]), TEXT, (40, y))
        draw_line(screen, fonts["text"], str(row["score"]), TEXT, (300, y))
        draw_line(screen, fonts["text"], str(row["level_reached"]), TEXT, (450, y))
        draw_line(screen, fonts["text"], str(row["result"]), TEXT, (600, y))
    if len(rows) == 0:
        draw_line(screen, fonts["text"], "No games saved yet", TEXT, (40, 130))
    draw_line(screen, fonts["text"], "M = menu", GREEN, (40, 570))


def draw_line(screen, font, text, colour, topleft):
    # Draw text with its top-left corner at the given point
    surface = font.render(text, True, colour)
    screen.blit(surface, topleft)
