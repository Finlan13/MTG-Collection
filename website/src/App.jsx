import { useEffect, useMemo, useState } from "react";


/* ============================================================
   CARD IMAGE
   ============================================================ */

function CardImage({ card }) {

  const [showBack, setShowBack] = useState(false);

  const frontImage = card.image_url;
  const backImage = card.back_image_url;

  const currentImage =
    showBack && backImage
      ? backImage
      : frontImage;

  if (!currentImage) {
    return (
      <div className="card-image-placeholder">
        No image available
      </div>
    );
  }

  return (
    <div className="card-image-container">

      <img
        className="card-image"
        src={currentImage}
        alt={
          showBack
            ? card.name + " reverse"
            : card.name
        }
        loading="lazy"
      />

      {backImage && (
        <button
          type="button"
          className="reverse-button"
          onClick={() =>
            setShowBack((current) => !current)
          }
        >
          {showBack ? "Front" : "Reverse"}
        </button>
      )}

    </div>
  );
}


/* ============================================================
   MAIN APP
   ============================================================ */

function App() {

  const [collection, setCollection] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(null);


  /* ==========================================================
     FILTER STATE
     ========================================================== */

  const [searchTerm, setSearchTerm] = useState("");

  const [selectedSet, setSelectedSet] = useState("All");

  const [selectedRarity, setSelectedRarity] = useState("All");

  const [selectedFoil, setSelectedFoil] = useState("All");

  const [selectedPrice, setSelectedPrice] = useState("All");


  /* ==========================================================
     SORT STATE
     ========================================================== */

  const [sortBy, setSortBy] = useState("name");

  const [sortDirection, setSortDirection] = useState("asc");


  /* ==========================================================
     LOAD COLLECTION
     ========================================================== */

  useEffect(() => {

    fetch(
      `${import.meta.env.BASE_URL}collection.json`
    )

      .then((response) => {

        if (!response.ok) {

          throw new Error(
            "Unable to load collection data."
          );

        }

        return response.json();

      })

      .then((data) => {

        if (!Array.isArray(data)) {

          throw new Error(
            "Collection data is not in the expected format."
          );

        }

        setCollection(data);

        setLoading(false);

      })

      .catch((err) => {

        setError(err.message);

        setLoading(false);

      });

  }, []);


  /* ==========================================================
     UNIQUE SETS
     ========================================================== */

  const sets = useMemo(() => {

    const values = collection
      .map((card) => card.set_name || card.set)
      .filter(Boolean);

    return [
      ...new Set(values)
    ].sort((a, b) =>
      String(a).localeCompare(String(b))
    );

  }, [collection]);


  /* ==========================================================
     UNIQUE RARITIES
     ========================================================== */

  const rarities = useMemo(() => {

    const values = collection
      .map((card) => card.rarity)
      .filter(Boolean);

    const rarityOrder = [
      "common",
      "uncommon",
      "rare",
      "mythic",
      "special",
      "bonus"
    ];

    return [
      ...new Set(values)
    ].sort((a, b) => {

      const indexA =
        rarityOrder.indexOf(
          String(a).toLowerCase()
        );

      const indexB =
        rarityOrder.indexOf(
          String(b).toLowerCase()
        );

      if (indexA === -1 && indexB === -1) {
        return String(a).localeCompare(String(b));
      }

      if (indexA === -1) {
        return 1;
      }

      if (indexB === -1) {
        return -1;
      }

      return indexA - indexB;

    });

  }, [collection]);


  /* ==========================================================
     TOTAL CARDS
     ========================================================== */

  const totalCards = useMemo(() => {

    return collection.reduce(
      (total, card) =>
        total +
        Number(card.qty || 0) +
        Number(card.qty_foil || 0),
      0
    );

  }, [collection]);


  /* ==========================================================
     UNIQUE CARDS
     ========================================================== */

  const uniqueCards = collection.length;


  /* ==========================================================
     COLLECTION VALUE
     ========================================================== */

  const collectionValue = useMemo(() => {

    return collection.reduce(
      (total, card) =>
        total +
        Number(card.current_value || 0),
      0
    );

  }, [collection]);


  /* ==========================================================
     FILTER + SORT
     ========================================================== */

  const filteredCollection = useMemo(() => {

    const search =
      searchTerm
        .trim()
        .toLowerCase();


    const filtered = collection.filter((card) => {

      /* ------------------------------------------------------
         SEARCH
         ------------------------------------------------------ */

      if (search) {

        const searchableText = [

          card.name,

          card.set,

          card.set_name,

          card.card_no,

          card.collector_number,

          card.artist,

          card.scryfall_artist

        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();


        if (
          !searchableText.includes(search)
        ) {

          return false;

        }

      }


      /* ------------------------------------------------------
         SET
         ------------------------------------------------------ */

      if (
        selectedSet !== "All"
      ) {

        const cardSet =
          card.set_name ||
          card.set;

        if (
          cardSet !== selectedSet
        ) {

          return false;

        }

      }


      /* ------------------------------------------------------
         RARITY
         ------------------------------------------------------ */

      if (
        selectedRarity !== "All"
      ) {

        if (
          String(card.rarity || "")
            .toLowerCase() !==
          String(selectedRarity)
            .toLowerCase()
        ) {

          return false;

        }

      }


      /* ------------------------------------------------------
         FOIL
         ------------------------------------------------------ */

      const regularQty =
        Number(card.qty || 0);

      const foilQty =
        Number(card.qty_foil || 0);


      if (
        selectedFoil === "Foil" &&
        foilQty <= 0
      ) {

        return false;

      }


      if (
        selectedFoil === "Non-Foil" &&
        regularQty <= 0
      ) {

        return false;

      }


      /* ------------------------------------------------------
         PRICE
         ------------------------------------------------------ */

      const price =
        Number(card.current_value || 0);


      if (
        selectedPrice === "Under $1" &&
        price >= 1
      ) {

        return false;

      }


      if (
        selectedPrice === "$1 - $5" &&
        (price < 1 || price > 5)
      ) {

        return false;

      }


      if (
        selectedPrice === "$5 - $10" &&
        (price < 5 || price > 10)
      ) {

        return false;

      }


      if (
        selectedPrice === "$10 - $25" &&
        (price < 10 || price > 25)
      ) {

        return false;

      }


      if (
        selectedPrice === "$25+"
        && price < 25
      ) {

        return false;

      }


      return true;

    });


    /* ========================================================
       SORT
       ======================================================== */

    filtered.sort((a, b) => {

      let valueA;
      let valueB;


      switch (sortBy) {

        case "price":

          valueA =
            Number(
              a.current_value || 0
            );

          valueB =
            Number(
              b.current_value || 0
            );

          break;


        case "quantity":

          valueA =
            Number(a.qty || 0) +
            Number(a.qty_foil || 0);

          valueB =
            Number(b.qty || 0) +
            Number(b.qty_foil || 0);

          break;


        case "set":

          valueA =
            String(
              a.set_name ||
              a.set ||
              ""
            ).toLowerCase();

          valueB =
            String(
              b.set_name ||
              b.set ||
              ""
            ).toLowerCase();

          break;


        case "rarity":

          const rarityOrder = {
            common: 1,
            uncommon: 2,
            rare: 3,
            mythic: 4,
            special: 5,
            bonus: 6
          };

          valueA =
            rarityOrder[
              String(
                a.rarity || ""
              ).toLowerCase()
            ] || 99;

          valueB =
            rarityOrder[
              String(
                b.rarity || ""
              ).toLowerCase()
            ] || 99;

          break;


        case "name":

        default:

          valueA =
            String(
              a.name || ""
            ).toLowerCase();

          valueB =
            String(
              b.name || ""
            ).toLowerCase();

          break;

      }


      if (
        typeof valueA === "string"
      ) {

        return (
          sortDirection === "asc"
            ? valueA.localeCompare(valueB)
            : valueB.localeCompare(valueA)
        );

      }


      return (
        sortDirection === "asc"
          ? valueA - valueB
          : valueB - valueA
      );

    });


    return filtered;

  }, [
    collection,
    searchTerm,
    selectedSet,
    selectedRarity,
    selectedFoil,
    selectedPrice,
    sortBy,
    sortDirection
  ]);


  /* ==========================================================
     RESET FILTERS
     ========================================================== */

  const resetFilters = () => {

    setSearchTerm("");

    setSelectedSet("All");

    setSelectedRarity("All");

    setSelectedFoil("All");

    setSelectedPrice("All");

    setSortBy("name");

    setSortDirection("asc");

  };


  /* ==========================================================
     LOADING
     ========================================================== */

  if (loading) {

    return (

      <main className="loading">

        <h1>
          MTG Collection
        </h1>

        <p>
          Loading collection...
        </p>

      </main>

    );

  }


  /* ==========================================================
     ERROR
     ========================================================== */

  if (error) {

    return (

      <main className="error">

        <h1>
          Unable to load collection
        </h1>

        <p>
          {error}
        </p>

      </main>

    );

  }


  /* ==========================================================
     WEBSITE
     ========================================================== */

  return (

    <main>


      {/* =====================================================
          HEADER
          ===================================================== */}

      <header className="header">

        <div>

          <h1>
            MTG Collection
          </h1>

          <p>
            My Magic: The Gathering collection
          </p>

        </div>

      </header>


      {/* =====================================================
          STATISTICS
          ===================================================== */}

      <section className="stats">

        <div className="stat-card">

          <span>
            Total Cards
          </span>

          <strong>
            {totalCards}
          </strong>

        </div>


        <div className="stat-card">

          <span>
            Unique Cards
          </span>

          <strong>
            {uniqueCards}
          </strong>

        </div>


        <div className="stat-card">

          <span>
            Collection Value
          </span>

          <strong>
            $
            {collectionValue.toFixed(2)}
          </strong>

        </div>

      </section>


      {/* =====================================================
          COLLECTION
          ===================================================== */}

      <section className="collection">


        {/* ===================================================
            COLLECTION HEADER
            =================================================== */}

        <div className="collection-header">

          <div>

            <h2>
              Collection
            </h2>

            <p className="result-count">

              Showing{" "}
              {filteredCollection.length}
              {" "}of{" "}
              {collection.length}
              {" "}unique cards

            </p>

          </div>


          {/* =================================================
              SEARCH
              ================================================= */}

          <div className="search-container">

            <input
              type="text"
              className="search-input"
              placeholder="Search cards..."
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(
                  event.target.value
                )
              }
              aria-label="Search cards"
            />


            {searchTerm && (

              <button
                type="button"
                className="clear-search"
                onClick={() =>
                  setSearchTerm("")
                }
                aria-label="Clear search"
              >
                ×
              </button>

            )}

          </div>

        </div>


        {/* ===================================================
            FILTERS
            =================================================== */}

        <div className="filters">


          {/* =================================================
              SET
              ================================================= */}

          <div className="filter-group">

            <label htmlFor="set-filter">
              Set
            </label>

            <select
              id="set-filter"
              value={selectedSet}
              onChange={(event) =>
                setSelectedSet(
                  event.target.value
                )
              }
            >

              <option value="All">
                All Sets
              </option>

              {sets.map((set) => (

                <option
                  key={set}
                  value={set}
                >
                  {set}
                </option>

              ))}

            </select>

          </div>


          {/* =================================================
              RARITY
              ================================================= */}

          <div className="filter-group">

            <label htmlFor="rarity-filter">
              Rarity
            </label>

            <select
              id="rarity-filter"
              value={selectedRarity}
              onChange={(event) =>
                setSelectedRarity(
                  event.target.value
                )
              }
            >

              <option value="All">
                All Rarities
              </option>

              {rarities.map((rarity) => (

                <option
                  key={rarity}
                  value={rarity}
                >
                  {String(rarity)
                    .charAt(0)
                    .toUpperCase() +
                    String(rarity)
                      .slice(1)}
                </option>

              ))}

            </select>

          </div>


          {/* =================================================
              FOIL
              ================================================= */}

          <div className="filter-group">

            <label htmlFor="foil-filter">
              Foil
            </label>

            <select
              id="foil-filter"
              value={selectedFoil}
              onChange={(event) =>
                setSelectedFoil(
                  event.target.value
                )
              }
            >

              <option value="All">
                All Cards
              </option>

              <option value="Non-Foil">
                Non-Foil
              </option>

              <option value="Foil">
                Foil
              </option>

            </select>

          </div>


          {/* =================================================
              PRICE
              ================================================= */}

          <div className="filter-group">

            <label htmlFor="price-filter">
              Price
            </label>

            <select
              id="price-filter"
              value={selectedPrice}
              onChange={(event) =>
                setSelectedPrice(
                  event.target.value
                )
              }
            >

              <option value="All">
                All Prices
              </option>

              <option value="Under $1">
                Under $1
              </option>

              <option value="$1 - $5">
                $1 - $5
              </option>

              <option value="$5 - $10">
                $5 - $10
              </option>

              <option value="$10 - $25">
                $10 - $25
              </option>

              <option value="$25+">
                $25+
              </option>

            </select>

          </div>


          {/* =================================================
              SORT
              ================================================= */}

          <div className="filter-group">

            <label htmlFor="sort-filter">
              Sort By
            </label>

            <select
              id="sort-filter"
              value={sortBy}
              onChange={(event) =>
                setSortBy(
                  event.target.value
                )
              }
            >

              <option value="name">
                Name
              </option>

              <option value="set">
                Set
              </option>

              <option value="price">
                Price
              </option>

              <option value="rarity">
                Rarity
              </option>

              <option value="quantity">
                Quantity
              </option>

            </select>

          </div>


          {/* =================================================
              SORT DIRECTION
              ================================================= */}

          <div className="filter-group">

            <label htmlFor="direction-filter">
              Order
            </label>

            <select
              id="direction-filter"
              value={sortDirection}
              onChange={(event) =>
                setSortDirection(
                  event.target.value
      
