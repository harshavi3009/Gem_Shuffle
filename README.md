# Gem Shuffle

Gem Shuffle is a game made with Python and Pygame. A gem is hidden under one of a row of bowls. The bowls shuffle, and you have to find the bowl that hides the gem. Every game is saved, so you can see your own Focus Report at the end, and the analysis notebook can study everyone's answers.

This guide is for Windows and assumes you have never used Python before. Follow the steps in order.

---

## 1. Install Python

1. Go to https://www.python.org/downloads/ and download **Python 3.12** for Windows.
2. Run the installer.
3. **Important:** on the first screen, tick the box **"Add python.exe to PATH"** at the bottom, then click **Install Now**.
4. When it says the setup was successful, click **Close**.

## 2. Open Command Prompt in the game folder

1. Open the folder that contains `main.py` in File Explorer.
2. Click in the **address bar** at the top (the path of the folder), type `cmd`, and press **Enter**.
3. A black window opens, already in the game folder. This window is called **Command Prompt**.

## 3. Install the libraries

In the Command Prompt window, type this line and press **Enter**:

```
pip install pygame pandas numpy jupyter
```

Wait until the text stops moving and you see the `>` prompt again. This can take a few minutes.

If `pygame` fails to install, type this instead:

```
pip install pygame-ce
```

then run the first command again without `pygame`:

```
pip install pandas numpy jupyter
```

## 4. Play the game

In the same Command Prompt window, type:

```
python main.py
```

and press **Enter**. The game window opens.

> **Always start the game from the folder that contains `main.py`.** The game looks for its data files in a folder called `data` next to where you start it. If you start it from somewhere else, it will not find them.

## 5. Open the analysis notebook

Close the game window, then in the same Command Prompt type:

```
jupyter notebook
```

Your web browser opens a list of files. Click **analysis.ipynb**. Run the cells from the top, one after another, using the **Run** button or by pressing **Shift + Enter**.

If `data/rounds.csv` and `data/games.csv` do not exist yet, the notebook uses **simulated demo data** so it still runs. Every heading in the notebook that says SIMULATED means fake numbers. Play the game first, and the real files will be used instead.

---

## Controls

### Menu
| Key | What it does |
|---|---|
| Letters, digits, spaces | Type your name (up to 12 characters) |
| Backspace | Delete the last letter |
| Enter | Start the game (an empty name becomes "Player") |
| L | Open the leaderboard (only when the name box is empty) |

### Playing
| Action | What it does |
|---|---|
| Watch the gem | The gem is shown under a bowl that is held to one side |
| Watch the shuffle | The bowls slide around each other. Some swaps are fake and do not change anything |
| Left-click a bowl | Choose that bowl |
| Number keys 1 to 5 | Choose the bowl in that numbered slot |
| Close the window | Quit the game |

### Report and leaderboard
| Key | What it does |
|---|---|
| R | Play again (on the report screen) |
| M | Go back to the menu |

---

## Scoring and lives

- You have **3 lives** (the red circles at the top). A wrong answer costs one life, and you stay on the same level.
- A correct answer scores **gem value × level number**. For example, a Ruby (value 10) on level 3 scores 30.
- Get **3 correct answers in a row** and your points are **doubled**.
- Find **every gem type** once and you get a **100-point bonus**.
- Pass all **10 levels** to win. Run out of lives and the game is lost.

---

## Where the files are saved

The game saves its data in the `data` folder, next to `main.py`:

| File | What is in it | When it is created |
|---|---|---|
| `data/rounds.csv` | One line for each round: the level, number of bowls, swaps, the answer, your choice and your reaction time | After your first game ends |
| `data/games.csv` | One line for each game: the player's name, score, level reached and result | After your first game ends |
| `data/levels_raw.csv` and `data/gems_raw.csv` | The level and gem settings. Do not change these. They are the starting data for the game | Already there |

The two `_raw` files contain some deliberate mistakes. The game fixes them in memory when it starts, and the files themselves are never changed.

You can open `rounds.csv` and `games.csv` in Excel or Notepad to see your results. Each game is added to the end of the file, so the files grow each time you play.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `'python' is not recognized` | Install Python again and make sure **"Add python.exe to PATH"** is ticked |
| `No module named pygame` | Run `pip install pygame` again, or `pip install pygame-ce` |
| The game says it cannot find `levels_raw.csv` | Start the game from the folder that contains `main.py`, and check that the `data` folder is there |
| The game closes straight away | Read the text in the Command Prompt window. It shows the error message |
