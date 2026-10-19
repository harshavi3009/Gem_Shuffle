# data.py
# Loads the two raw CSV files and cleans them.
# The raw files have deliberate mistakes. We fix them in memory only;
# the CSV files themselves are never changed.

import os
import numpy as np
import pandas as pd


def load_levels(path=os.path.join("data", "levels_raw.csv")):
    # Step 1: if the file is missing, say so and stop
    if not os.path.exists(path):
        print("Cannot find {} - check the data folder.".format(path))
        return None

    # Step 2: read the CSV into a table (a DataFrame)
    df = pd.read_csv(path)

    # Step 3: strange symbols like ?? and ## become NaN
    # (NaN means "Not a Number", which pandas uses for missing values)
    df = df.replace(["??", "##"], np.nan)

    # Step 4: the word "five" is in the wrong format, so change it to "5"
    df["cups"] = df["cups"].replace("five", "5")

    # Step 5: remove the repeated row, then sort by level
    # reset_index gives the rows the numbers 0, 1, 2... again
    df = df.drop_duplicates()
    df = df.sort_values("level").reset_index(drop=True)

    # Step 6: change the four columns to float so they can hold NaN
    for col in ["cups", "swaps", "swap_ms", "fakes"]:
        df[col] = df[col].astype(float)

    # Show how many missing values there are before filling them
    print("Missing values before filling:")
    print(df.isnull().sum())

    # Step 7: fill missing swaps and swap_ms with the average of the
    # previous and next level. Levels must get harder in order, so we
    # do not use the column median (that would make level 7 easier
    # than level 6).
    for col in ["swaps", "swap_ms"]:
        for i in df.index:
            if pd.isnull(df.loc[i, col]):
                previous_value = df.loc[i - 1, col]
                next_value = df.loc[i + 1, col]
                df.loc[i, col] = round((previous_value + next_value) / 2)

    # Show the missing values again, now they should all be gone
    print("Missing values after filling:")
    print(df.isnull().sum())

    # Step 8: the values are whole numbers, so change them back to int
    for col in ["cups", "swaps", "swap_ms", "fakes"]:
        df[col] = df[col].astype(int)

    # Step 9: give back the cleaned table
    return df


def load_gems(path=os.path.join("data", "gems_raw.csv")):
    # Step 1: if the file is missing, say so and stop
    if not os.path.exists(path):
        print("Cannot find {} - check the data folder.".format(path))
        return None

    # Step 2: read the CSV and replace strange symbols with NaN
    df = pd.read_csv(path)
    df = df.replace(["??", "##"], np.nan)

    # Step 3: remove extra spaces and make each name start with a capital,
    # so " emerald " becomes "Emerald"
    df["gem"] = df["gem"].apply(lambda x: x.strip().title())

    # Step 4: remove the repeated Ruby row, keep the first one
    df = df.drop_duplicates(subset=["gem"], keep="first")

    # Step 5: change value and rarity_weight to float so they can hold NaN
    df["value"] = df["value"].astype(float)
    df["rarity_weight"] = df["rarity_weight"].astype(float)

    # Step 6: a missing value is filled with the middle value (median) of
    # the column. round() makes it a whole number.
    df["value"] = df["value"].fillna(round(df["value"].median()))

    # Step 7: a missing rarity is filled with the smallest weight.
    # Unknown rarity is treated as the rarest gem.
    df["rarity_weight"] = df["rarity_weight"].fillna(df["rarity_weight"].min())

    # Step 8: give back the cleaned table (5 rows)
    return df


def load_all():
    # Load both files and turn each table into a list of dictionaries.
    # A dictionary is one row, like {"gem": "Ruby", "value": 10.0, ...}
    levels_df = load_levels()
    gems_df = load_gems()

    # If a file was missing, there is nothing to play with
    if levels_df is None or gems_df is None:
        return None, None

    levels_list = levels_df.to_dict("records")
    gems_list = gems_df.to_dict("records")
    return levels_list, gems_list
