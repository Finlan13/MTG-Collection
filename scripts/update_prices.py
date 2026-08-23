import json
import time
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_FILE = Path("output/collection.json")

SCRYFALL_DELAY = 0.11

SCRYFALL_HEADERS = {
    "User-Agent": "MTG-Collection/1.0",
    "Accept": "application/json"
}

MAX_RETRIES = 5


# ============================================================
# LOAD COLLECTION
# ============================================================

print("=" * 60)
print("MTG COLLECTION - PRICE UPDATE")
print("=" * 60)
print()

if not COLLECTION_FILE.exists():

    raise FileNotFoundError(
        "output/collection.json was not found."
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
# IDENTIFY UNIQUE SCRYFALL IDS
# ============================================================

scryfall_ids = sorted(
    {
        record.get("scryfall_id")
        for record in collection
        if record.get("scryfall_id")
    }
)


print(
    f"Unique cards requiring prices: "
    f"{len(scryfall_ids)}"
)

print()


# ============================================================
# GET PRICES
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
        f"{scryfall_id}"
    )


    url = (
        "https://api.scryfall.com/cards/"
        f"{scryfall_id}"
    )


    success = False


    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = requests.get(
                url,
                headers=SCRYFALL_HEADERS,
                timeout=30
            )


            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                card_prices = data.get(
                    "prices",
                    {}
                )


                prices[scryfall_id] = {

                    "usd":
                        card_prices.get("usd"),

                    "usd_foil":
                        card_prices.get(
                            "usd_foil"
                        )
                }


                successful += 1

                success = True

                break


            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )


                if retry_after:

                    try:

                        wait_seconds = float(
                            retry_after
                        )

                    except ValueError:

                        wait_seconds = (
                            5 * attempt
                        )

                else:

                    wait_seconds = (
                        5 * attempt
                    )


                print(
                    f"  Rate limited. "
                    f"Waiting {wait_seconds:.1f}s..."
                )


                time.sleep(
                    wait_seconds
                )

                continue


            # ------------------------------------------------
            # OTHER HTTP ERROR
            # ------------------------------------------------

            print(
                f"  HTTP {response.status_code}"
            )

            break


        except requests.RequestException as error:

            print(
                f"  Request error: {error}"
            )


            wait_seconds = (
                2 * attempt
            )


            time.sleep(
                wait_seconds
            )


    if not success:

        failed += 1


    # --------------------------------------------------------
    # SPACE REQUESTS
    # --------------------------------------------------------

    time.sleep(
        SCRYFALL_DELAY
    )


# ============================================================
# UPDATE COLLECTION
# ============================================================

print()
print("Updating collection values...")
print()


updated = 0
price_missing = 0


for record in collection:

    scryfall_id = record.get(
        "scryfall_id"
    )


    if not scryfall_id:

        continue


    if scryfall_id not in prices:

        continue


    price = prices[
        scryfall_id
    ]


    usd = price.get(
        "usd"
    )

    usd_foil = price.get(
        "usd_foil"
    )


    # ========================================================
    # QUANTITIES
    # ========================================================

    qty = record.get(
        "qty",
        0
    )

    qty_foil = record.get(
        "qty_foil",
        0
    )


    try:

        qty = float(qty)

    except (
        ValueError,
        TypeError
    ):

        qty = 0


    try:

        qty_foil = float(qty_foil)

    except (
        ValueError,
        TypeError
    ):

        qty_foil = 0


    # ========================================================
    # NON-FOIL VALUE
    # ========================================================

    if usd is not None:

        nonfoil_value = (
            qty * float(usd)
        )

    else:

        nonfoil_value = None

        price_missing += 1


    # ========================================================
    # FOIL VALUE
    # ========================================================

    if usd_foil is not None:

        foil_value = (
            qty_foil
            * float(usd_foil)
        )

    else:

        foil_value = None


    # ========================================================
    # CURRENT VALUE
    # ========================================================

    values = []


    if nonfoil_value is not None:

        values.append(
            nonfoil_value
        )


    if foil_value is not None:

        values.append(
            foil_value
        )


    if values:

        current_value = sum(
            values
        )

    else:

        current_value = None


    # ========================================================
    # UPDATE RECORD
    # ========================================================

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
    f"Collection records:     "
    f"{len(collection)}"
)

print(
    f"Unique cards requested: "
    f"{len(scryfall_ids)}"
)

print(
    f"Successful requests:    "
    f"{successful}"
)

print(
    f"Failed requests:        "
    f"{failed}"
)

print(
    f"Collection records updated: "
    f"{updated}"
)

print(
    f"Cards without USD price: "
    f"{price_missing}"
)

print()
