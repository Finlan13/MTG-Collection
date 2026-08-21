import json
import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data/collection.xlsx")
OUTPUT_FILE = Path("output/collection.json")
ERROR_FILE = Path("output/import_errors.csv")

HEADERS = {
    "User-Agent": "MTG Collection Tracker/1.0",
    "Accept": "application/json"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def number_or_zero(value):
    """
    Convert a value to a number.
    Blank cells, None and NaN become 0.
    """

    if pd.isna(value):
        return 0.0

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def number_or_none(value):
    """
    Convert a value to a number.
    Blank cells, None and NaN become None.
    """

    if pd.isna(value):
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


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
# READ EXCEL
# ============================================================

print("Reading collection...")

df = pd.read_excel(INPUT_FILE)

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
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

df["CardNo"] = (
    df["CardNo"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df = df[
    (df["Set"] != "") &
    (df["CardNo"] != "")
]


# ============================================================
# UNIQUE CARD PRINTINGS
# ============================================================

unique_cards = (
    df[
        ["Set", "CardNo"]
    ]
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

name_mismatches = []

artist_mismatches = []


for _, row in unique_cards.iterrows():

    set_code = row["Set"]

    card_number = row["CardNo"]

    key = f"{set_code}-{card_number}"

    url = (
        "https://api.scryfall.com/cards/"
        f"{set_code}/{card_number}"
    )

    print(
        f"Looking up: "
        f"{set_code.upper()} "
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

            prices = card.get(
                "prices",
                {}
            )

            scryfall_cards[key] = {

                "scryfall_id":
                    card.get("id"),

                "scryfall_name":
                    card.get("name"),

                "scryfall_set":
                    card.get("set"),

                "set_name":
                    card.get("set_name"),

                "collector_number":
                    card.get(
                        "collector_number"
                    ),

                "rarity":
                    card.get("rarity"),

                "mana_cost":
                    card.get("mana_cost"),

                "type_line":
                    card.get("type_line"),

                "oracle_text":
                    card.get(
                        "oracle_text"
                    ),

                "scryfall_artist":
                    card.get("artist"),

                "image_url":
                    card
                    .get("image_uris", {})
                    .get("normal"),

                "scryfall_url":
                    card.get(
                        "scryfall_uri"
                    ),

                "usd":
                    number_or_none(
                        prices.get("usd")
                    ),

                "usd_foil":
                    number_or_none(
                        prices.get("usd_foil")
                    )
            }

        else:

            errors.append({

                "type":
                    "Scryfall API error",

                "set":
                    set_code,

                "card_no":
                    card_number,

                "status_code":
                    response.status_code,

                "error":
                    response.text
            })

    except requests.RequestException as error:

        errors.append({

            "type":
                "Request error",

            "set":
                set_code,

            "card_no":
                card_number,

            "status_code":
                None,

            "error":
                str(error)
        })

    time.sleep(0.1)


# ============================================================
# BUILD OUTPUT
# ============================================================

output = []

total_cost_basis = 0.0

total_current_value = 0.0


for _, row in df.iterrows():

    set_code = row["Set"]

    card_number = row["CardNo"]

    key = f"{set_code}-{card_number}"

    card_data = scryfall_cards.get(key)


    # ========================================================
    # COLLECTION QUANTITIES
    # ========================================================

    qty = number_or_zero(
        row["Qty"]
    )

    qty_foil = number_or_zero(
        row["Qty (Foil)"]
    )


    # ========================================================
    # PURCHASE PRICE
    # ========================================================

    purchase_price = number_or_none(
        row["PurchasePrice"]
    )


    # ========================================================
    # COST BASIS
    # ========================================================

    if purchase_price is not None:

        cost_basis = (
            (qty + qty_foil)
            * purchase_price
        )

    else:

        cost_basis = None


    # ========================================================
    # DEFAULT VALUES
    # ========================================================

    usd = None

    usd_foil = None

    nonfoil_value = 0.0

    foil_value = 0.0

    current_value = 0.0

    unrealised_gain_loss = None


    # ========================================================
    # SCRYFALL DATA
    # ========================================================

    if card_data:

        usd = card_data["usd"]

        usd_foil = card_data[
            "usd_foil"
        ]


        # ----------------------------------------------------
        # NON-FOIL VALUE
        # ----------------------------------------------------

        if usd is not None:

            nonfoil_value = (
                qty * usd
            )


        # ----------------------------------------------------
        # FOIL VALUE
        # ----------------------------------------------------

        if usd_foil is not None:

            foil_value = (
                qty_foil * usd_foil
            )


        # ----------------------------------------------------
        # CURRENT VALUE
        # ----------------------------------------------------

        current_value = (
            nonfoil_value +
            foil_value
        )


        # ----------------------------------------------------
        # GAIN / LOSS
        # ----------------------------------------------------

        if cost_basis is not None:

            unrealised_gain_loss = (
                current_value -
                cost_basis
            )


        # ====================================================
        # NAME VALIDATION
        # ====================================================

        excel_name = normalise_text(
            row["Name"]
        )

        scryfall_name = normalise_text(
            card_data[
                "scryfall_name"
            ]
        )

        if (
            excel_name !=
            scryfall_name
        ):

            name_mismatches.append({

                "type":
                    "Name mismatch",

                "id":
                    row["ID"],

                "set":
                    set_code,

                "card_no":
                    card_number,

                "excel_name":
                    row["Name"],

                "scryfall_name":
                    card_data[
                        "scryfall_name"
                    ]
            })


        # ====================================================
        # ARTIST VALIDATION
        # ====================================================

        if (
            "Artist" in df.columns
            and pd.notna(
                row["Artist"]
            )
            and str(
                row["Artist"]
            ).strip() != ""
        ):

            excel_artist = (
                normalise_text(
                    row["Artist"]
                )
            )

            scryfall_artist = (
                normalise_text(
                    card_data[
                        "scryfall_artist"
                    ]
                )
            )

            if (
                excel_artist !=
                scryfall_artist
            ):

                artist_mismatches.append({

                    "type":
                        "Artist mismatch",

                    "id":
                        row["ID"],

                    "set":
                        set_code,

                    "card_no":
                        card_number,

                    "excel_artist":
                        row["Artist"],

                    "scryfall_artist":
                        card_data[
                            "scryfall_artist"
                        ]
                })


    # ========================================================
    # OUTPUT RECORD
    # ========================================================

    record = {

        "id":
            row["ID"],

        "set":
            set_code,

        "card_no":
            card_number,

        "name":
            row["Name"],

        "artist":
            (
                row["Artist"]
                if (
                    "Artist" in df.columns
                    and pd.notna(
                        row["Artist"]
                    )
                )
                else None
            ),

        "qty":
            qty,

        "qty_foil":
            qty_foil,

        "acquisition_date":
            (
                row["AcquisitionDate"]
                .isoformat()
                if (
                    pd.notna(
                        row[
                            "AcquisitionDate"
                        ]
                    )
                    and hasattr(
                        row[
                            "AcquisitionDate"
                        ],
                        "isoformat"
                    )
                )
                else None
            ),

        "purchase_price":
            purchase_price,

        "cost_basis":
            cost_basis,

        "notes":
            (
                row["Notes"]
                if (
                    "Notes" in df.columns
                    and pd.notna(
                        row["Notes"]
                    )
                )
                else None
            ),

        # Scryfall
        "scryfall_match":
            bool(card_data),

        "scryfall_id":
            (
                card_data[
                    "scryfall_id"
                ]
                if card_data
                else None
            ),

        "scryfall_name":
            (
                card_data[
                    "scryfall_name"
                ]
                if card_data
                else None
            ),

        "scryfall_set":
            (
                card_data[
                    "scryfall_set"
                ]
                if card_data
                else None
            ),

        "set_name":
            (
                card_data[
                    "set_name"
                ]
                if card_data
                else None
            ),

        "collector_number":
            (
                card_data[
                    "collector_number"
                ]
                if card_data
                else None
            ),

        "rarity":
            (
                card_data[
                    "rarity"
                ]
                if card_data
                else None
            ),

        "mana_cost":
            (
                card_data[
                    "mana_cost"
                ]
                if card_data
                else None
            ),

        "type_line":
            (
                card_data[
                    "type_line"
                ]
                if card_data
                else None
            ),

        "oracle_text":
            (
                card_data[
                    "oracle_text"
                ]
                if card_data
                else None
            ),

        "scryfall_artist":
            (
                card_data[
                    "scryfall_artist"
                ]
                if card_data
                else None
            ),

        "image_url":
            (
                card_data[
                    "image_url"
                ]
                if card_data
                else None
            ),

        "scryfall_url":
            (
                card_data[
                    "scryfall_url"
                ]
                if card_data
                else None
            ),

        # Pricing
        "usd":
            usd,

        "usd_foil":
            usd_foil,

        # Valuation
        "nonfoil_value":
            nonfoil_value,

        "foil_value":
            foil_value,

        "current_value":
            current_value,

        "unrealised_gain_loss":
            unrealised_gain_loss
    }


    output.append(record)


    # ========================================================
    # TOTALS
    # ========================================================

    if cost_basis is not None:

        total_cost_basis += (
            cost_basis
        )


    total_current_value += (
        current_value
    )


# ============================================================
# FINAL NaN / INF CLEANUP
# ============================================================

def clean_for_json(value):

    if isinstance(
        value,
        float
    ):

        if pd.isna(value):

            return None

        if value == float("inf"):

            return None

        if value == float("-inf"):

            return None

    return value


for record in output:

    for key in record:

        record[key] = clean_for_json(
            record[key]
        )


# ============================================================
# SAVE JSON
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
        ensure_ascii=False,
        allow_nan=False
    )


# ============================================================
# SAVE ERRORS
# ============================================================

all_errors = []

all_errors.extend(
    errors
)

all_errors.extend(
    name_mismatches
)

all_errors.extend(
    artist_mismatches
)


if all_errors:

    pd.DataFrame(
        all_errors
    ).to_csv(
        ERROR_FILE,
        index=False
    )


# ============================================================
# SUMMARY
# ============================================================

successful_matches = (
    len(scryfall_cards)
)

missing_usd_count = sum(

    1

    for card
    in scryfall_cards.values()

    if card["usd"] is None
)

missing_foil_price_count = sum(

    1

    for card
    in scryfall_cards.values()

    if card["usd_foil"] is None
)


print()

print("=" * 60)

print(
    "MTG COLLECTION IMPORT COMPLETE"
)

print("=" * 60)

print()

print(
    f"Collection rows:          "
    f"{len(df)}"
)

print(
    f"Unique printings:         "
    f"{len(unique_cards)}"
)

print(
    f"Scryfall matches:         "
    f"{successful_matches}"
)

print(
    f"Scryfall errors:          "
    f"{len(errors)}"
)

print(
    f"Name mismatches:          "
    f"{len(name_mismatches)}"
)

print(
    f"Artist mismatches:        "
    f"{len(artist_mismatches)}"
)

print(
    f"Missing USD prices:       "
    f"{missing_usd_count}"
)

print(
    f"Missing foil prices:      "
    f"{missing_foil_price_count}"
)

print()

print(
    f"Total cost basis:         "
    f"${total_cost_basis:,.2f}"
)

print(
    f"Total current value:      "
    f"${total_current_value:,.2f}"
)

print(
    f"Unrealised gain/loss:     "
    f"${total_current_value - total_cost_basis:,.2f}"
)

print()

print(
    f"Created: {OUTPUT_FILE}"
)

if all_errors:

    print(
        f"Exceptions: {ERROR_FILE}"
    )
