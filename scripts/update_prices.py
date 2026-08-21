import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_FILE = Path("output/collection.json")
PRICE_HISTORY_FILE = Path("output/price_history.json")


SCRYFALL_HEADERS = {
    "User-Agent": "MTG-Collection/1.0",
    "Accept": "application/json"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def number_or_zero(value):
    """
    Convert blank/non-numeric values to zero.
    """

    if value is None:
        return 0.0

    try:

        if pd.isna(value):
            return 0.0

    except (TypeError, ValueError):

        pass

    try:
        return float(value)

    except (ValueError, TypeError):

        return 0.0


def number_or_none(value):
    """
    Convert blank/non-numeric values to None.
    """

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):

        pass

    try:
        return float(value)

    except (ValueError, TypeError):

        return None


# ============================================================
# START
# ============================================================

print("=" * 60)
print("MTG COLLECTION - PRICE UPDATE")
print("=" * 60)
print()


# ============================================================
# LOAD COLLECTION
# ============================================================

if not COLLECTION_FILE.exists():

    raise FileNotFoundError(
        "collection.json does not exist."
    )


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
# LOAD EXISTING PRICE HISTORY
# ============================================================

if PRICE_HISTORY_FILE.exists():

    with open(
        PRICE_HISTORY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        price_history = json.load(file)

else:

    price_history = []


print(
    f"Existing price records: "
    f"{len(price_history)}"
)

print()


# ============================================================
# CREATE CURRENT SNAPSHOT DATE
# ============================================================

now = datetime.now(
    timezone.utc
)

snapshot_date = now.strftime(
    "%Y-%m-%d"
)

snapshot_timestamp = now.isoformat()


print(
    f"Snapshot date: {snapshot_date}"
)

print()


# ============================================================
# GET UNIQUE SCRYFALL IDS
# ============================================================

scryfall_ids = sorted(
    {
        record.get("scryfall_id")
        for record in collection
        if record.get("scryfall_id")
    }
)


print(
    f"Unique Scryfall cards: "
    f"{len(scryfall_ids)}"
)

print()


# ============================================================
# REMOVE EXISTING SNAPSHOT FOR TODAY
# ============================================================

price_history = [
    record
    for record in price_history
    if record.get("snapshot_date")
    != snapshot_date
]


# ============================================================
# GET CURRENT PRICES
# ============================================================

prices = {}

successful = 0
failed = 0


for index, scryfall_id in enumerate(
    scryfall_ids,
    start=1
):

    print(
        f"[{index}/{len(scryfall_ids)}] "
        f"Getting price for "
        f"{scryfall_id}"
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


        if response.status_code != 200:

            print(
                f"  ERROR: "
                f"HTTP {response.status_code}"
            )

            failed += 1

            continue


        data = response.json()

        scryfall_prices = data.get(
            "prices",
            {}
        )


        usd = number_or_none(
            scryfall_prices.get("usd")
        )

        usd_foil = number_or_none(
            scryfall_prices.get("usd_foil")
        )


        prices[scryfall_id] = {
            "usd": usd,
            "usd_foil": usd_foil
        }


        # ----------------------------------------------------
        # STORE HISTORICAL SNAPSHOT
        # ----------------------------------------------------

        price_history.append(
            {
                "snapshot_date":
                    snapshot_date,

                "snapshot_timestamp":
                    snapshot_timestamp,

                "scryfall_id":
                    scryfall_id,

                "usd":
                    usd,

                "usd_foil":
                    usd_foil
            }
        )


        successful += 1


    except requests.RequestException as error:

        print(
            f"  ERROR: {error}"
        )

        failed += 1


# ============================================================
# SAVE PRICE HISTORY
# ============================================================

with open(
    PRICE_HISTORY_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        price_history,
        file,
        indent=2,
        ensure_ascii=False,
        allow_nan=False
    )


print()
print(
    f"Price history records: "
    f"{len(price_history)}"
)

print()


# ============================================================
# UPDATE COLLECTION VALUES
# ============================================================

print(
    "Updating collection valuations..."
)

updated = 0


for record in collection:

    scryfall_id = record.get(
        "scryfall_id"
    )


    if not scryfall_id:

        continue


    price = prices.get(
        scryfall_id
    )


    if not price:

        continue


    usd = price.get(
        "usd"
    )

    usd_foil = price.get(
        "usd_foil"
    )


    qty = number_or_zero(
        record.get("qty")
    )

    qty_foil = number_or_zero(
        record.get("qty_foil")
    )

    cost_basis = number_or_none(
        record.get("cost_basis")
    )


    # --------------------------------------------------------
    # NON-FOIL VALUE
    # --------------------------------------------------------

    if usd is not None:

        nonfoil_value = (
            qty * usd
        )

    else:

        nonfoil_value = 0.0


    # --------------------------------------------------------
    # FOIL VALUE
    # --------------------------------------------------------

    if usd_foil is not None:

        foil_value = (
            qty_foil * usd_foil
        )

    else:

        foil_value = 0.0


    # --------------------------------------------------------
    # CURRENT VALUE
    # --------------------------------------------------------

    current_value = (
        nonfoil_value
        + foil_value
    )


    # --------------------------------------------------------
    # UNREALISED GAIN / LOSS
    # --------------------------------------------------------

    if cost_basis is not None:

        unrealised_gain_loss = (
            current_value
            - cost_basis
        )

    else:

        unrealised_gain_loss = None


    # --------------------------------------------------------
    # UPDATE RECORD
    # --------------------------------------------------------

    record["usd"] = usd

    record["usd_foil"] = usd_foil

    record["nonfoil_value"] = (
        nonfoil_value
    )

    record["foil_value"] = (
        foil_value
    )

    record["current_value"] = (
        current_value
    )

    record["unrealised_gain_loss"] = (
        unrealised_gain_loss
    )


    updated += 1


# ============================================================
# SAVE COLLECTION
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
print("PRICE UPDATE COMPLETE")
print("=" * 60)
print()

print(
    f"Cards requested:    {len(scryfall_ids)}"
)

print(
    f"Successful prices:  {successful}"
)

print(
    f"Failed prices:      {failed}"
)

print(
    f"Collection updated: {updated}"
)

print()

print(
    "Price history and collection "
    "have been updated."
)

print()
