import json
import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/Collection.xlsx")
CARD_FILE = Path("output/cards.json")

SCRYFALL_HEADERS = {
    "User-Agent": "MTG-Collection/1.0",
    "Accept": "application/json"
}

SCRYFALL_DELAY = 0.1


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """
    Convert pandas values into JSON-safe values.
    """

    if pd.isna(value):
        return None

    return value


def normalise_text(value):
    """
    Normalise text for comparison.
    """

    if pd.isna(value):
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


# ============================================================
# LOAD EXISTING CARD MASTER
# ============================================================

print("=" * 60)
print("MTG COLLECTION - CARD MASTER IMPORT")
print("=" * 60)
print()

CARD_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


if CARD_FILE.exists():

    print("Loading existing card master...")

    with open(
        CARD_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        cards = json.load(file)

else:

    print("No existing card master found.")
    print("Creating a new card master.")

    cards = []


# ============================================================
# CREATE LOOKUP INDEX
# ============================================================

card_index = {}

for card in cards:

    key = (
        f"{normalise_text(card.get('set'))}|"
        f"{normalise_text(card.get('collector_number'))}"
    )

    card_index[key] = card


print(
    f"Existing cards in master: "
    f"{len(card_index)}"
)

print()


# ============================================================
# READ COLLECTION
# ============================================================

print("Reading Excel collection...")

df = pd.read_excel(
    INPUT_FILE
)

df = df.dropna(
    how="all"
)


# ============================================================
# VALIDATE COLUMNS
# ============================================================

required_columns = [
    "Set",
    "CardNo",
    "Name"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )


# ============================================================
# NORMALISE SET / CARD NUMBER
# ============================================================

df["_set"] = (
    df["Set"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

df["_card_no"] = (
    df["CardNo"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

df = df[
    (df["_set"] != "") &
    (df["_card_no"] != "")
]


# ============================================================
# FIND UNIQUE CARD PRINTINGS
# ============================================================

unique_cards = (
    df[
        ["_set", "_card_no"]
    ]
    .drop_duplicates()
)


print(
    f"Collection rows: "
    f"{len(df)}"
)

print(
    f"Unique card printings: "
    f"{len(unique_cards)}"
)

print()


# ============================================================
# DETERMINE WHICH CARDS ARE NEW
# ============================================================

new_cards = []

existing_cards = 0


for _, row in unique_cards.iterrows():

    key = (
        f"{row['_set']}|"
        f"{row['_card_no']}"
    )

    if key in card_index:

        existing_cards += 1

    else:

        new_cards.append(
            (
                row["_set"],
                row["_card_no"]
            )
        )


print(
    f"Already in card master: "
    f"{existing_cards}"
)

print(
    f"New cards requiring Scryfall: "
    f"{len(new_cards)}"
)

print()


# ============================================================
# SCRYFALL LOOKUPS - NEW CARDS ONLY
# ============================================================

successful = 0
failed = 0


for index, (
    set_code,
    card_number
) in enumerate(
    new_cards,
    start=1
):

    print(
        f"[{index}/{len(new_cards)}] "
        f"Looking up "
        f"{set_code.upper()} "
        f"{card_number}"
    )


    url = (
        "https://api.scryfall.com/cards/"
        f"{set_code}/{card_number}"
    )


    try:

        response = requests.get(
            url,
            headers=SCRYFALL_HEADERS,
            timeout=20
        )


        if response.status_code != 200:

            print(
                f"  ERROR: "
                f"Scryfall returned "
                f"{response.status_code}"
            )

            failed += 1

            continue


        data = response.json()


        # ====================================================
        # EXTRACT CARD DATA
        # ====================================================

        image_uris = data.get(
            "image_uris",
            {}
        )


        card = {

            "scryfall_id":
                data.get("id"),

            "set":
                data.get("set"),

            "set_name":
                data.get("set_name"),

            "collector_number":
                data.get(
                    "collector_number"
                ),

            "name":
                data.get("name"),

            "artist":
                data.get("artist"),

            "rarity":
                data.get("rarity"),

            "mana_cost":
                data.get("mana_cost"),

            "type_line":
                data.get("type_line"),

            "oracle_text":
                data.get("oracle_text"),

            "image_url":
                image_uris.get(
                    "normal"
                ),

            "scryfall_url":
                data.get(
                    "scryfall_uri"
                )
        }


        # ====================================================
        # ADD TO MASTER
        # ====================================================

        key = (
            f"{normalise_text(set_code)}|"
            f"{normalise_text(card_number)}"
        )


        card_index[key] = card

        cards.append(card)

        successful += 1


    except requests.RequestException as error:

        print(
            f"  ERROR: {error}"
        )

        failed += 1


    time.sleep(
        SCRYFALL_DELAY
    )


# ============================================================
# SAVE CARD MASTER
# ============================================================

print()
print("Saving card master...")


with open(
    CARD_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        cards,
        file,
        indent=2,
        ensure_ascii=False,
        allow_nan=False
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("IMPORT COMPLETE")
print("=" * 60)
print()

print(
    f"Collection rows:       {len(df)}"
)

print(
    f"Unique cards:          {len(unique_cards)}"
)

print(
    f"Existing cards reused: {existing_cards}"
)

print(
    f"New cards found:       {successful}"
)

print(
    f"Failed lookups:        {failed}"
)

print(
    f"Total cards in master: {len(cards)}"
)

print()

print(
    f"Created: {CARD_FILE}"
)

print()
