# Gem Shuffle — Build Instructions for Claude Code

You are building **Gem Shuffle**, a Pygame version of the classic shell game, for a 2nd-year B.Tech (CSE) Software Lab miniproject. Three beginner students must **explain every line in a viva**, so simplicity and clarity matter more than cleverness or performance.

Read this whole file before writing any code. Follow the design exactly. If something is ambiguous, choose the simplest option and leave a comment saying what you chose.

> **Camera angle: TOP-DOWN.** The camera looks straight down at the table top, as if it were hanging from the ceiling. This is not a front or side view. Every bowl is seen from above, so it looks like a **circle** (a round rim around a darker inner circle). The gem is a small shape lying flat on the table. Because there is no height on screen, "lifting" a bowl is shown by sliding it aside with a soft shadow, and a swap is shown by the two bowls sliding **around each other on the table surface** in curved paths, one bending towards the top of the screen and the other towards the bottom. They never pass "over" or "under" each other. Section 6A has the details.

---

## 1. Hard rules for the code

1. **Libraries:** Python 3.10+, `pygame` (or `pygame-ce`), `pandas`, `numpy`, and the standard library (`math`, `os`, `datetime`). Nothing else.
2. **No classes.** Use only lists, dictionaries, tuples, sets and functions. The students have not studied OOP in depth.
3. **Short functions.** Aim for under ~30 lines each, one clear job per function.
4. **Comment every block** in plain English that a beginner can read aloud in a viva.
5. Prefer `"{}".format(...)` for building strings (that is what the course taught). Avoid f-strings, list/dict comprehensions longer than one simple line, `lambda` beyond the cleaning step, decorators, generators, type hints, `*args`/`**kwargs`, and `global` where a return value works.
6. **No hard-coded game balance.** Level settings and gem values must come from the CSV files.
7. **Missing images must not crash the game.** If a PNG is missing, draw the object with `pygame.draw` shapes instead, as seen from above: bowl = two `pygame.draw.circle` calls (outer rim, darker inner disc), gem = a small `pygame.draw.polygon` diamond.
8. The game must run with `python main.py` on **Windows**. Use relative paths built with `os.path.join`.

The concepts the code must visibly use, so the students can point to them: variables/operators, if/elif/else, while/for loops, lists, tuples, strings, sets (including set difference), dictionaries, functions with default arguments and multiple return values, lambda, the `math` module, file handling with append mode and `os.path.exists`, NumPy (`linspace`, `random.choice` with and without `replace`, weighted `random.choice`, `randint`, array maths, boolean arrays, `mean`, `percentile`), and Pandas (`read_csv`, `replace`, `astype`, `isnull`, `fillna`, `.loc`, `drop_duplicates`, `sort_values`, `reset_index`, `to_dict("records")`, `DataFrame`, `groupby`, `idxmax`, `corr`).

---

## 2. Folder structure

```
GemShuffle/
├── main.py            # starts the game, game loop, screens (state) and round phases (phase)
├── settings.py        # constants only
├── data.py            # load + clean levels_raw.csv and gems_raw.csv
├── game.py            # bowls, swaps, animation maths, clicks, scoring
├── report.py          # save to CSV, Focus Report stats, leaderboard
├── analysis.ipynb     # the attention experiment notebook
├── README.md          # how to install and run (Windows, beginner level)
├── data/
│   ├── levels_raw.csv
│   └── gems_raw.csv   # rounds.csv and games.csv are created by the game
└── assets/            # all images TOP-DOWN views (optional): bowl.png (a bowl seen from above, ~100x100),
                       # ruby.png, emerald.png, sapphire.png, diamond.png, laddoo.png (~40x40), table.png (wood texture)
```

---

## 3. Input data files (create exactly these)

The mistakes are **intentional**; they exist so the cleaning code has something to fix. Do not fix them in the CSV.

`data/levels_raw.csv`
```
level,cups,swaps,swap_ms,fakes
1,3,3,700,0
2,3,5,600,0
2,3,5,600,0
3,3,7,500,0
4,3,8,??,1
5,4,8,450,1
6,4,10,400,1
7,4,,350,2
8,5,12,320,2
9,five,14,280,2
10,5,16,250,3
```

`data/gems_raw.csv`
```
gem,value,rarity_weight,image
Ruby,10,40,ruby.png
 emerald ,15,30,emerald.png
Sapphire,##,20,sapphire.png
Diamond,40,8,diamond.png
Golden Laddoo,60,,laddoo.png
Ruby,10,40,ruby.png
```

---

## 4. `settings.py`

```python
SCREEN = (900, 600)          # tuple: window size
FPS = 60
LIVES = 3
# TOP-DOWN view: the screen is the table top seen from above.
TABLE_Y = 320                # y of the row where the bowls rest on the table
BOWL_R = 48                  # bowl radius in pixels (bowls are circles from above)
ARC = 70                     # how far (in px) the two bowls curve apart while sliding around each other
LIFT_ASIDE = (0, -95)        # a lifted bowl is drawn slid this far from its spot (shows the gem beneath)
SHADOW_ALPHA = 70            # transparency of the soft shadow under a lifted / moving bowl
SHOW_MS = 1500               # gem visible before the round starts
COVER_MS = 600               # bowl coming down
REVEAL_MS = 1500             # bowls lifted after the choice
STREAK_FOR_BONUS = 3
COLLECTOR_BONUS = 100
# colours as RGB tuples: background, table, bowl, text, gold, red, green
```

---

## 5. `data.py` — cleaning (must match exactly)

### `load_levels(path=os.path.join("data", "levels_raw.csv"))`
1. If the file does not exist (`os.path.exists`), print a clear message and return `None`.
2. `df = pd.read_csv(path)`
3. `df = df.replace(["??", "##"], np.nan)`: abnormal symbols become NaN
4. `df["cups"] = df["cups"].replace("five", "5")`: wrong format
5. `df = df.drop_duplicates()`, then `df = df.sort_values("level").reset_index(drop=True)`
6. Convert `cups, swaps, swap_ms, fakes` with `astype(float)`
7. Fill missing `swaps` and `swap_ms` with the **average of the previous and next level**, using a plain loop over `df.index` and `df.loc[i, col]`, then `round()`. (Reason, for a comment: levels must get harder in order; the column median would make level 7 easier than level 6.)
8. Convert the four columns back with `astype(int)`.
9. Print `isnull().sum()` before and after filling (useful for the demo).
10. Return the DataFrame.

The expected clean result has 10 rows. Level 4 `swap_ms` becomes **475**, level 7 `swaps` becomes **11**, and level 9 `cups` becomes **5**.

### `load_gems(path=os.path.join("data", "gems_raw.csv"))`
1. Same existence check, `read_csv`, `replace(["??", "##"], np.nan)`
2. `df["gem"] = df["gem"].apply(lambda x: x.strip().title())`
3. `df = df.drop_duplicates(subset=["gem"], keep="first")`
4. `value` and `rarity_weight` to float
5. Fill `value` with `round(median)`, which gives **28** for Sapphire. Fill `rarity_weight` with the column **min**, which gives **8** for Golden Laddoo. (Comment: unknown rarity is treated as the rarest.)
6. Return the DataFrame (5 rows).

### `load_all()`
Returns `(levels_list, gems_list)`, built with `to_dict("records")`.

---

## 6. Core game logic (`game.py`)

### Data shapes

```python
bowl  = {"id": 0, "slot": 0}                 # id never changes, slot changes on every swap
move  = (slot_a, slot_b, is_fake)            # a tuple
round_ = {
  "level": 5, "cups": 4, "swaps": 8, "fakes": 1, "swap_ms": 450,
  "cups_list": [bowl, ...], "slots_x": [150.0, 350.0, 550.0, 750.0],
  "gem": {gem dict}, "gem_cup": 2, "start_slot": 2,
  "moves": [move, ...], "move_index": 0,
  "phase": "show", "phase_start": ms, "choose_start": ms,
  "chosen_slot": None, "answer_slot": None, "correct": None,
  "reaction_s": None, "points": 0, "second": 0
}
game = {
  "id": int, "player": str, "date": "YYYY-MM-DD",
  "score": 0, "lives": 3, "streak": 0, "best_streak": 0,
  "level_index": 0, "gems_won": set(), "bonus_given": False,
  "rounds": [], "result": None
}
```

### Functions

- **`new_round(level, gems)`**
  - Builds `cups_list` with `id == slot == i`.
  - `slots_x = list(np.linspace(150, 750, level["cups"]))`.
  - Gem: `weights = np.array([...rarity_weight...])`, then `np.random.choice(len(gems), p=weights / weights.sum())`.
  - `gem_cup = int(np.random.randint(0, cups))`.
  - `moves = make_swaps(level)`, `phase = "show"`.
- **`make_swaps(level)`**
  - Builds `level["swaps"]` real moves using `np.random.choice(level["cups"], 2, replace=False)` → `(int(a), int(b), False)`.
  - For each fake, picks a pair the same way and inserts it at `np.random.randint(0, len(moves) + 1)` with `list.insert`.
- **`bowl_position(start_x, end_x, t, goes_up, fake)`** (top-down view; see Section 6A)
  - Returns `(x, y)`, the bowl's centre on the table.
  - Real move: `x = start_x + (end_x - start_x) * t`.
  - Fake move: `x = start_x + (end_x - start_x) * 0.5 * math.sin(math.pi * t)`, which goes halfway and comes back.
  - `curve = ARC * math.sin(math.pi * t)`, which is 0 at the start, ARC in the middle, and 0 at the end.
  - The bowl with `goes_up = True` uses `y = TABLE_Y - curve` and bends towards the top of the screen. The other uses `y = TABLE_Y + curve` and bends towards the bottom. Together they slide around each other like two hands circling cups on a table, and they never overlap because they are always `2 * curve` apart vertically in the middle of the move.
- **`finish_swap(cups_list, a, b)`**: swaps the `slot` values of the bowls currently in slots `a` and `b`.
- **`answer_slot(round_)`**: returns the slot of the bowl whose `id == gem_cup`.
- **`finish_round(chosen_bowl, round_, game, gems_count)`**
  - Sets `chosen_slot`, `answer_slot`, `correct` (1/0) and `reaction_s` (2 d.p.).
  - **If correct:** `streak += 1`, update `best_streak`, `points = value * level`, doubled if `streak >= STREAK_FOR_BONUS`. Then `score += points`, add the gem name to `gems_won`, and give the collector bonus once when `len(gems_won) == gems_count`. Finally `level_index += 1`.
  - **If wrong:** `lives -= 1`, `streak = 0`, and the level index is unchanged.
  - Appends `round_` to `game["rounds"]` and sets `phase = "reveal"`.
- **`bowl_rect(x)`**: returns `pygame.Rect(x - BOWL_R, TABLE_Y - BOWL_R, 2 * BOWL_R, 2 * BOWL_R)`, the square around the bowl's circle, used with `collidepoint(event.pos)`.

### 6A. Drawing in the top-down view

- **Table:** fill the window with a wood-brown colour, or blit `table.png`. Optionally draw a faint darker felt rectangle behind the row of bowls.
- **Resting bowl** at `(x, TABLE_Y)`: blit `bowl.png` centred there. Without the image, draw `pygame.draw.circle(screen, RIM_COLOUR, (x, y), BOWL_R)` and then a darker inner circle of radius `BOWL_R - 10`.
- **Shadow:** draw a soft shadow under any bowl that is moving or lifted. Use a dark circle on a small `pygame.Surface` with `set_alpha(SHADOW_ALPHA)`, offset 6 px right and 6 px down from the bowl, drawn **before** the bowl. This one detail makes the top-down view read clearly.
- **Gem:** the gem lies flat on the table at its bowl's slot. It is drawn **only** when its bowl is lifted (show and reveal phases) and is always drawn *before* the bowl, so a covering bowl hides it.
- **Lifted bowl** (show phase, and reveal for the chosen bowl and the gem's bowl): draw the gem at the slot, then the shadow, then the bowl shifted by `LIFT_ASIDE` and scaled up about 10% with `pygame.transform.scale`. It looks as if it has been picked up and held to one side.
- **Cover phase:** animate the bowl from the lifted-aside position back onto its slot over `COVER_MS`, moving it in a straight line from `(x, TABLE_Y) + LIFT_ASIDE` to `(x, TABLE_Y)`.
- **Swapping bowls:** draw both at `bowl_position(...)` with shadows. The first slot of the move uses `goes_up=True` and the second uses `goes_up=False`. Optional touch: `scale = 1 + 0.06 * math.sin(math.pi * t)` makes them look briefly raised mid-slide.
- **Slot numbers:** draw `1`, `2`, `3`… in small text just below each resting slot (at `TABLE_Y + BOWL_R + 18`) to match the number-key controls.
- **Drawing order each frame:** table → slot numbers → visible gems → shadows → resting bowls → moving or lifted bowls → HUD. Draw moving bowls last so they sit on top.

### Round phases (in `main.py`)

`show` (SHOW_MS: the gem's bowl is drawn lifted aside, with the gem visible on the table) → `cover` (COVER_MS: that bowl slides back on top of the gem) → `shuffle` → `choose` → `reveal` (REVEAL_MS) → next round.

During **shuffle**, `t = (now - phase_start) / swap_ms` (clamp to 1). The two bowls in the current move's slots are drawn at `bowl_position(...)`; all others are drawn at rest. At `t >= 1`: if the move is not fake, call `finish_swap`; then `move_index += 1` and `phase_start = now`. When `move_index == len(moves)`, go to `choose` and set `choose_start`.

During **choose**, a mouse click inside a bowl's rect, or the number keys `1`–`5` (slot index), calls `finish_round`.

After **reveal**:
- If `lives == 0`, set `result = "lost"`.
- If `level_index == 10`, set `result = "won"`.
- If either is set, save the game and switch to the report. Otherwise start a new round at `levels[level_index]`.

**Self-check to include as `test_tracking()` in game.py:** run 1,000 random rounds without drawing. Track the gem a second way, with a list `order` where `order[slot] = bowl id`, and swap entries on real moves. Assert both methods agree on the final slot. Run it once from `main.py` behind a `DEBUG = False` flag.

---

## 7. Screens (`main.py`)

A `state` string decides what to draw:

- **`"menu"`**: Title "Gem Shuffle", a text box where the player types a name (letters, digits and spaces, max 12 characters, Backspace works), short how-to-play lines, "Enter = play", "L = leaderboard".
- **`"play"`**: Table background, the bowls, and the gem during show/reveal. The HUD shows: Level n / 10, hearts for lives, Streak, Score, and the current gem's name. The phase text shows "Watch the gem…", "Shuffling 6 / 9", or "Pick a bowl!". On reveal, show "Correct! +90" or "Wrong!" in green or red.
- **`"report"`**: The Focus Report (Section 8). "R = play again", "M = menu".
- **`"leaderboard"`**: Top 5 rows of `games.csv` sorted by score: player, score, level reached, result. "M = menu".

The game loop shape must be obvious:

```python
while running:
    # 1. EVENTS
    # 2. UPDATE  (depends on state / phase)
    # 3. DRAW    (depends on state / phase)
    pygame.display.flip()
    clock.tick(FPS)
```

Load images and fonts **once**, before the loop.

---

## 8. Saving and the Focus Report (`report.py`)

### `save_game(game)`
- Appends **one line per round** to `data/rounds.csv` using `open(path, "a")`, writing the header only if `not os.path.exists(path)`:
  `game_id,player,date,level,cups,swaps,fakes,swap_ms,gem,start_slot,answer_slot,chosen_slot,correct,reaction_s,points`
- Appends **one line** to `data/games.csv` the same way:
  `game_id,player,date,score,level_reached,rounds,correct,best_streak,avg_reaction_s,gems_won,result`
- Builds each line with `"{},{},...\n".format(...)`. Strip commas out of player names before writing.
- `game_id`: 1 + the number of rows already in `games.csv`, or 1 if the file doesn't exist.

### `focus_report(game, gems_list)`
Returns a dictionary:
- `better_than`: `round((scores < game["score"]).mean() * 100)`, where `scores = np.array(pd.read_csv(games.csv)["score"])`
- `accuracy`: `rounds["correct"].mean() * 100`, where `rounds = pd.DataFrame(game["rounds"])`
- `avg_reaction`: the mean of `reaction_s`; `slow_decision` is `np.percentile(reaction_s, 90)`
- `favourite_slot` and its share: `rounds.groupby("chosen_slot").size()` → `idxmax()` and `max() / len`
- `gems_collected`: `len(game["gems_won"])`; `still_to_find`: `set(all gem names) - game["gems_won"]`
- `acc_by_cups`: `pd.read_csv(rounds.csv).groupby("cups")["correct"].mean() * 100` (all players)

Handle the edge cases: zero rounds, and a CSV that has only one row.

### Drawing the report
Draw text rows for each statistic. Add a simple horizontal bar chart of `acc_by_cups`, drawn with `pygame.draw.rect`, with the longest bar 130 px and the others scaled to it. Label each bar "3 bowls 81%" and so on.

---

## 9. `analysis.ipynb`

A clean notebook with a markdown heading before every cell explaining what it does. It reads `data/rounds.csv` and `data/games.csv`. If they are missing, it generates **clearly-labelled simulated demo data** so the notebook runs before anyone has played; mark this loudly as "SIMULATED – replace by playing the game".

Sections, in order:
1. **Load and inspect:** `shape`, `dtypes`, `head(4)`, `tail(4)`.
2. **Cleaning demo:** call `load_levels` / `load_gems`; show `isnull().sum()` before and after, and the clean tables.
3. **Descriptive stats:** `describe()`, mean, median, mode, var and skew of `reaction_s` and `score`.
4. **Experiment questions:**
   - accuracy by `level`, by `cups` and by `fakes` (`groupby` + mean)
   - position bias in 3-bowl rounds (`groupby("chosen_slot").size()` vs a fair 1/3)
   - shuffle fairness (`groupby("answer_slot").size()`)
   - reaction time of correct vs wrong rounds
   - `(start_slot == answer_slot).mean()`
5. **Extremes:** fastest correct round and slowest round (`idxmin` / `idxmax`); leaderboard via `sort_values`.
6. **Correlation:** a `corr()` matrix of level, cups, swaps, fakes, swap_ms, reaction_s and correct.
7. **Pearson r by hand** for `swaps` vs `correct`, using the formula `r = (nΣxy − ΣxΣy) / sqrt((nΣx² − (Σx)²)(nΣy² − (Σy)²))` with NumPy, then compared with `.corr()`.
8. **New column:** `shuffle_s = (swaps + fakes) * swap_ms / 1000`; accuracy by shuffle length; top 5 games by score.
9. **Findings:** a markdown cell with placeholders for the students to fill in.

---

## 10. README.md (for beginners on Windows)

Explain, step by step and with no assumed knowledge:
- install Python 3.12 with "Add python.exe to PATH" ticked
- open Command Prompt in the folder (type `cmd` in the Explorer address bar)
- `pip install pygame pandas numpy jupyter` (if pygame fails, use `pip install pygame-ce`)
- `python main.py` to run the game
- `jupyter notebook` to open the analysis

Also list the controls, and explain where the CSV files are saved.

---

## 11. Build order and checks

1. `settings.py`, then `data.py`. Run `load_levels()` and `load_gems()` and confirm the expected values in Section 5.
2. `game.py`, then run `test_tracking()`; it must pass.
3. `main.py`: menu, then play with shapes only, then add images.
4. `report.py`: play two games and confirm `rounds.csv` and `games.csv` are created correctly and the report shows sensible numbers.
5. `analysis.ipynb`: run every cell top to bottom.
6. `README.md`.

After each file, give the students a short **beginner-level explanation of what the file does**, function by function, so they can study it.
