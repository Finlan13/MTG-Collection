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
COLLECTION_FILE = Path("output/collection.json")

SCRYFALL_HEADERS = {
    "User-Agent": "MTG-Collection/1.0",
    "Accept": "application/json"
}

SCRYFALL_DELAY = 0.1


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_blank(value):
    """
    Return True when a value is blank, None or NaN.
    """

    if value is None:
        return True

    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def number_or_zero(value):
    """
    Convert blank/non-numeric values to zero.
    """

    if is_blank(value):
        return 0.0

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def number_or_none(value):
    """
    Convert blank/non-numeric values to None.
    """

    if is_blank(value):
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def text_or_none(value):
    """
    Convert blank values to None.
    """

    if is_blank(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    return text


def date_or_none(value):
    """
    Convert Excel dates to ISO format.
    """

    if is_blank(value):
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def normalise_text(value):
    """
    Normalise text for matching.
    """

    if is_blank(value):
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


# ============================================================
# START
# ============================================================

print("=" * 60)
print("MTG COLLECTION - COLLECTION IMPORT")
print("=" * 60)
print()


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

CARD_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD EXISTING CARD MASTER
# ============================================================

if CARD_FILE.exists():

    print("Loading existing card master...")

    with open(
        CARD_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        cards = json.load(file)

else:

    print(
        "No card master found. "
        "A new one will be created."
    )

    cards = []


# ============================================================
# CREATE CARD LOOKUP
# ============================================================

card_index = {}

for card in cards:

    key = (
        f"{normalise_text(card.get('set'))}|"
        f"{normalise_text(card.get('collector_number'))}"
    )

    card_index[key] = card


print(
    f"Existing cards in master: {len(card_index)}"
)

print()


# ============================================================
# READ EXCEL COLLECTION
# ============================================================

print("Reading Excel collection...")

df = pd.read_excel(
    INPUT_FILE
)

df = df.dropna(
    how="all"
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [
    "ID",
    "Set",
    "CardNo",
    "Name",
    "Qty",
    "Qty (Foil)",
    "AcquisitionDate",
    "PurchasePrice"
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
# NORMALISE SET AND CARD NUMBER
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
# FIND UNIQUE CARDS
# ============================================================

unique_cards = (
    df[
        ["_set", "_card_no"]
    ]
    .drop_duplicates()
)


print(
    f"Collection rows: {len(df)}"
)

print(
    f"Unique card printings: {len(unique_cards)}"
)

print()


# ============================================================
# FIND NEW CARDS
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
    f"Already in card master: {existing_cards}"
)

print(
    f"New cards requiring Scryfall: {len(new_cards)}"
)

print()


# ============================================================
# LOOK UP NEW CARDS
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
                image_uris.get("normal"),

            "scryfall_url":
                data.get("scryfall_uri")
        }


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
# BUILD COLLECTION.JSON
# ============================================================

print()
print("Building collection.json...")


collection = []

matched = 0
unmatched = 0


for _, row in df.iterrows():

    set_code = (
        str(row["Set"])
        .strip()
        .lower()
    )

    card_number = (
        str(row["CardNo"])
        .strip()
    )


    key = (
        f"{normalise_text(set_code)}|"
        f"{normalise_text(card_number)}"
    )


    card = card_index.get(key)


    if card:

        matched += 1

    else:

        unmatched += 1


    qty = number_or_zero(
        row["Qty"]
    )

    qty_foil = number_or_zero(
        row["Qty (Foil)"]
    )

    purchase_price = number_or_none(
        row["PurchasePrice"]
    )


    # --------------------------------------------------------
    # COST BASIS
    # --------------------------------------------------------

    if purchase_price is not None:

        cost_basis = (
            (qty + qty_foil)
            * purchase_price
        )

    else:

        cost_basis = None


    # --------------------------------------------------------
    # COLLECTION RECORD
    # --------------------------------------------------------

    record = {

        "id":
            text_or_none(
                row["ID"]
            ),

        "set":
            set_code,

        "card_no":
            card_number,

        "name":
            text_or_none(
                row["Name"]
            ),

        "artist":
            (
                text_or_none(
                    row["Artist"]
                )
                if "Artist" in df.columns
                else None
            ),

        "qty":
            qty,

        "qty_foil":
            qty_foil,

        "acquisition_date":
            date_or_none(
                row["AcquisitionDate"]
            ),

        "purchase_price":
            purchase_price,

        "cost_basis":
            cost_basis,

        "notes":
            (
                text_or_none(
                    row["Notes"]
                )
                if "Notes" in df.columns
                else None
            ),

        "scryfall_match":
            bool(card),

        "scryfall_id":
            (
                card.get("scryfall_id")
                if card
                else None
            ),

        "scryfall_name":
            (
                card.get("name")
                if card
                else None
            ),

        "scryfall_set":
            (
                card.get("set")
                if card
                else None
            ),

        "set_name":
            (
                card.get("set_name")
                if card
                else None
            ),

        "collector_number":
            (
                card.get("collector_number")
                if card
                else None
            ),

        "rarity":
            (
                card.get("rarity")
                if card
                else None
            ),

        "mana_cost":
            (
                card.get("mana_cost")
                if card
                else None
            ),

        "type_line":
            (
                card.get("type_line")
                if card
                else None
            ),

        "oracle_text":
            (
                card.get("oracle_text")
                if card
                else None
            ),

        "scryfall_artist":
            (
                card.get("artist")
                if card
                else None
            ),

        "image_url":
            (
                card.get("image_url")
                if card
                else None
            ),

        "scryfall_url":
            (
                card.get("scryfall_url")
                if card
                else None
            )
    }


    collection.append(
        record
    )


# ============================================================
# SAVE COLLECTION.JSON
# ============================================================

with open(
    COLLECTION_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        collection,
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
print("COLLECTION IMPORT COMPLETE")
print("=" * 60)
print()

print(
    f"Collection rows:       {len(collection)}"
)

print(
    f"Existing cards reused: {existing_cards}"
)

print(
    f"New cards added:       {successful}"
)

print(
    f"Failed Scryfall calls: {failed}"
)

print(
    f"Matched collection:    {matched}"
)

print(
    f"Unmatched collection:  {unmatched}"
)

print()

print(
    f"Card master: {CARD_FILE}"
)

print(
    f"Collection:  {COLLECTION_FILE}"
)

print()

print(
    "Prices are managed separately "
    "by update_prices.py."
)

print()
