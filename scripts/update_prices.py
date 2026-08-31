import json
import time
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

CARD_FILE = Path("output/cards.json")
COLLECTION_FILE = Path("output/collection.json")

SCRYFALL_HEADERS = {
    "User-Agent": "MTG-Collection/1.0",
    "Accept": "application/json",
}

# Scryfall asks clients to avoid excessive request rates.
# We only request prices for unique Scryfall IDs.
SCRYFALL_DELAY = 0.1


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def number_or_zero(value):
    """
    Convert a value to float.
    Return 0.0 for blank or invalid values.
    """

    if value is None:
        return 0.0

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def price_or_none(value):
    """
    Convert a Scryfall price to a float.
    Return None when no price is available.
    """

    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ============================================================
# START
# ============================================================

print("=" * 60)
print("MTG COLLECTION - UPDATE PRICES")
print("=" * 60)
print()


# ============================================================
# CHECK FILES
# ============================================================

if not CARD_FILE.exists():
    raise FileNotFoundError(
        f"Card master not found: {CARD_FILE}"
    )

if not COLLECTION_FILE.exists():
    raise FileNotFoundError(
        f"Collection file not found: {COLLECTION_FILE}"
    )


# ============================================================
# LOAD CARD MASTER
# ============================================================

print("Loading card master...")

with open(
    CARD_FILE,
    "r",
    encoding="utf-8"
) as file:

    cards = json.load(file)


print(
    f"Cards in master: {len(cards)}"
)

print()


# ============================================================
# LOAD COLLECTION
# ============================================================

print("Loading collection...")

with open(
    COLLECTION_FILE,
    "r",
    encoding="utf-8"
) as file:

    collection = json.load(file)


print(
    f"Collection records: {len(collection)}"
)

print()


# ============================================================
# CREATE SCRYFALL ID LOOKUP
# ============================================================

card_ids = set()

for card in collection:

    scryfall_id = card.get("scryfall_id")

    if scryfall_id:
        card_ids.add(scryfall_id)


print(
    f"Unique Scryfall cards requiring price checks: "
    f"{len(card_ids)}"
)

print()


# ============================================================
# UPDATE PRICES FROM SCRYFALL
# ============================================================

prices = {}

successful = 0
failed = 0


for index, scryfall_id in enumerate(
    sorted(card_ids),
    start=1
):

    print(
        f"[{index}/{len(card_ids)}] "
        f"Getting price for {scryfall_id}"
    )

    url = (
        "https://api.scryfall.com/cards/"
        f"{scryfall_id}"
    )

    try:

        response = requests.get(
            url,
            headers=SCRYFALL_HEADERS,
            timeout=20
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if response.status_code == 200:

            data = response.json()

            scryfall_prices = data.get(
                "prices",
                {}
            )

            usd = price_or_none(
                scryfall_prices.get("usd")
            )

            usd_foil = price_or_none(
                scryfall_prices.get("usd_foil")
            )

            prices[scryfall_id] = {
                "usd": usd,
                "usd_foil": usd_foil,
            }

            successful += 1

            print(
                f"  USD: {usd}"
            )

            print(
                f"  USD Foil: {usd_foil}"
            )

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        elif response.status_code == 429:

            print(
                "  ERROR: HTTP 429 - "
                "Scryfall rate limit reached."
            )

            failed += 1

            # Wait longer before continuing.
            time.sleep(2)

            continue

        # ----------------------------------------------------
        # OTHER ERROR
        # ----------------------------------------------------

        else:

            print(
                f"  ERROR: Scryfall returned "
                f"{response.status_code}"
            )

            failed += 1

    except requests.RequestException as error:

        print(
            f"  ERROR: {error}"
        )

        failed += 1

    # --------------------------------------------------------
    # REQUEST DELAY
    # --------------------------------------------------------

    time.sleep(
        SCRYFALL_DELAY
    )


# ============================================================
# UPDATE COLLECTION RECORDS
# ============================================================

print()
print("Updating collection values...")
print()


updated_records = 0


for card in collection:

    scryfall_id = card.get(
        "scryfall_id"
    )

    if not scryfall_id:
        continue

    if scryfall_id not in prices:
        continue

    price_data = prices[scryfall_id]

    usd = price_data.get(
        "usd"
    )

    usd_foil = price_data.get(
        "usd_foil"
    )

    qty = number_or_zero(
        card.get("qty")
    )

    qty_foil = number_or_zero(
        card.get("qty_foil")
    )


    # --------------------------------------------------------
    # STORE CURRENT PRICES
    # --------------------------------------------------------

    card["price_usd"] = usd
    card["price_usd_foil"] = usd_foil


    # --------------------------------------------------------
    # CALCULATE CURRENT VALUE
    # --------------------------------------------------------

    regular_value = (
        qty * usd
        if usd is not None
        else 0.0
    )

    foil_value = (
        qty_foil * usd_foil
        if usd_foil is not None
        else 0.0
    )

    current_value = (
        regular_value +
        foil_value
    )


    card["current_value"] = (
        round(
            current_value,
            2
        )
    )


    updated_records += 1


# ============================================================
# SAVE COLLECTION
# ============================================================

print(
    "Saving updated collection..."
)

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
print("PRICE UPDATE COMPLETE")
print("=" * 60)
print()

print(
    f"Collection records:       {len(collection)}"
)

print(
    f"Unique cards checked:     {len(card_ids)}"
)

print(
    f"Successful Scryfall calls:{successful}"
)

print(
    f"Failed Scryfall calls:    {failed}"
)

print(
    f"Records updated:          {updated_records}"
)

print()

print(
    f"Updated file: "
    f"{COLLECTION_FILE}"
)

print()
