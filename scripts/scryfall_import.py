import json
import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/Collection.xlsx")
OUTPUT_FILE = Path("output/collection.json")
ERROR_FILE = Path("output/import_errors.csv")

HEADERS = {
    "User-Agent": "MTG Collection Tracker/1.0",
    "Accept": "application/json"
}


# ============================================================
# READ EXCEL
# ============================================================

print("Reading collection...")

df = pd.read_excel(INPUT_FILE)

# Remove completely empty rows
df = df.dropna(how="all")


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
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# PREPARE DATA
# ============================================================

df["Set"] = (
    df["Set"]
    .astype(str)
    .str.strip()
    .str.lower()
)

df["CardNo"] = (
    df["CardNo"]
    .astype(str)
    .str.strip()
)

# Remove rows without a Set or CardNo
df = df[
    (df["Set"] != "") &
    (df["CardNo"] != "")
]


# ============================================================
# FIND UNIQUE CARD PRINTINGS
# ============================================================

unique_cards = (
    df[["Set", "CardNo"]]
    .drop_duplicates()
)

print(
    f"Unique card printings found: "
    f"{len(unique_cards)}"
)


# ============================================================
# QUERY SCRYFALL
# ============================================================

scryfall_cards = {}
errors = []


for _, row in unique_cards.iterrows():

    set_code = row["Set"]
    card_number = row["CardNo"]

    key = f"{set_code}-{card_number}"

    url = (
        "https://api.scryfall.com/cards/"
        f"{set_code}/{card_number}"
    )

    print(
        f"Looking up: {set_code.upper()} "
        f"{card_number}"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code == 200:

            card = response.json()

            scryfall_cards[key] = {
                "scryfall_id": card.get("id"),
                "scryfall_name": card.get("name"),
                "scryfall_set": card.get("set"),
                "set_name": card.get("set_name"),
                "collector_number": card.get(
                    "collector_number"
                ),
                "rarity": card.get("rarity"),
                "mana_cost": card.get("mana_cost"),
                "type_line": card.get("type_line"),
                "oracle_text": card.get("oracle_text"),
                "scryfall_artist": card.get("artist"),

                "image_url": (
                    card.get("image_uris", {})
                    .get("normal")
                ),

                "scryfall_url": card.get(
                    "scryfall_uri"
                ),

                "usd": (
                    card.get("prices", {})
                    .get("usd")
                ),

                "usd_foil": (
                    card.get("prices", {})
                    .get("usd_foil")
                )
            }

        else:

            errors.append({
                "set": set_code,
                "card_no": card_number,
                "status_code": response.status_code,
                "error": response.text
            })

    except requests.RequestException as error:

        errors.append({
            "set": set_code,
            "card_no": card_number,
            "status_code": None,
            "error": str(error)
        })

    # Keep requests below Scryfall's
    # recommended API rate.
    time.sleep(0.1)


# ============================================================
# COMBINE EXCEL + SCRYFALL
# ============================================================

output = []

for _, row in df.iterrows():

    set_code = row["Set"]
    card_number = row["CardNo"]

    key = f"{set_code}-{card_number}"

    card_data = scryfall_cards.get(key)

    record = {
        "id": row["ID"],
        "set": set_code,
        "card_no": card_number,
        "name": row["Name"],
        "artist": (
            row["Artist"]
            if "Artist" in df.columns
            and pd.notna(row["Artist"])
            else None
        ),
        "qty": (
            row["Qty"]
            if pd.notna(row["Qty"])
            else 0
        ),
        "qty_foil": (
            row["Qty (Foil)"]
            if pd.notna(row["Qty (Foil)"])
            else 0
        ),
        "acquisition_date": (
            row["AcquisitionDate"].isoformat()
            if pd.notna(row["AcquisitionDate"])
            and hasattr(
                row["AcquisitionDate"],
                "isoformat"
            )
            else None
        ),
        "purchase_price": (
            row["PurchasePrice"]
            if pd.notna(row["PurchasePrice"])
            else None
        ),
        "notes": (
            row["Notes"]
            if "Notes" in df.columns
            and pd.notna(row["Notes"])
            else None
        )
    }

    if card_data:
        record.update(card_data)
        record["scryfall_match"] = True

    else:
        record["scryfall_match"] = False

    output.append(record)


# ============================================================
# SAVE COLLECTION.JSON
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# SAVE ERRORS
# ============================================================

if errors:

    pd.DataFrame(errors).to_csv(
        ERROR_FILE,
        index=False
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 50)
print("IMPORT COMPLETE")
print("=" * 50)

print(f"Collection rows: {len(df)}")
print(f"Unique printings: {len(unique_cards)}")
print(
    f"Scryfall matches: "
    f"{len(scryfall_cards)}"
)
print(
    f"Scryfall errors: "
    f"{len(errors)}"
)

print()
print(f"Created: {OUTPUT_FILE}")

if errors:
    print(f"Errors: {ERROR_FILE}")
