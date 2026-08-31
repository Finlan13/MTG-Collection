import { useEffect, useMemo, useState } from "react";

// ============================================================
// CARD IMAGE
// ============================================================

function CardImage({ card }) {
const [showBack, setShowBack] = useState(false);

const frontImage = card.image_url;
const backImage = card.back_image_url;

const currentImage =
showBack && backImage
? backImage
: frontImage;

if (!currentImage) {
return ( <div className="card-image-placeholder">
No image available </div>
);
}

return ( <div className="card-image-container">

```
  <img
    className="card-image"
    src={currentImage}
    alt={
      showBack
        ? `${card.name} reverse`
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
```

);
}

// ============================================================
// APP
// ============================================================

function App() {

const [collection, setCollection] = useState([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

// ==========================================================
// FILTERS
// ==========================================================

const [searchTerm, setSearchTerm] = useState("");
const [selectedSet, setSelectedSet] = useState("All");
const [selectedRarity, setSelectedRarity] = useState("All");
const [selectedPrice, setSelectedPrice] = useState("All");

const [sortBy, setSortBy] = useState("name-asc");

// ==========================================================
// LOAD COLLECTION
// ==========================================================

useEffect(() => {

```
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

    setCollection(data);
    setLoading(false);

  })

  .catch((err) => {

    setError(err.message);
    setLoading(false);

  });
```

}, []);

// ==========================================================
// SET OPTIONS
// ==========================================================

const setOptions = useMemo(() => {

```
const sets = collection
  .map((card) => card.set)
  .filter(Boolean);

return [
  "All",
  ...Array.from(new Set(sets)).sort()
];
```

}, [collection]);

// ==========================================================
// RARITY OPTIONS
// ==========================================================

const rarityOptions = useMemo(() => {

```
const rarities = collection
  .map((card) => card.rarity)
  .filter(Boolean);

return [
  "All",
  ...Array.from(new Set(rarities)).sort()
];
```

}, [collection]);

// ==========================================================
// FILTERED + SORTED COLLECTION
// ==========================================================

const filteredCollection = useMemo(() => {

```
let result = [...collection];

// --------------------------------------------------------
// SEARCH
// --------------------------------------------------------

const search = searchTerm
  .trim()
  .toLowerCase();

if (search) {

  result = result.filter((card) => {

    return (
      String(card.name || "")
        .toLowerCase()
        .includes(search) ||

      String(card.set_name || "")
        .toLowerCase()
        .includes(search) ||

      String(card.set || "")
        .toLowerCase()
        .includes(search) ||

      String(card.card_no || "")
        .toLowerCase()
        .includes(search) ||

      String(card.artist || "")
        .toLowerCase()
        .includes(search) ||

      String(card.rarity || "")
        .toLowerCase()
        .includes(search)
    );

  });

}


// --------------------------------------------------------
// SET
// --------------------------------------------------------

if (selectedSet !== "All") {

  result = result.filter(
    (card) =>
      String(card.set || "")
        .toLowerCase() ===
      selectedSet.toLowerCase()
  );

}


// --------------------------------------------------------
// RARITY
// --------------------------------------------------------

if (selectedRarity !== "All") {

  result = result.filter(
    (card) =>
      String(card.rarity || "")
        .toLowerCase() ===
      selectedRarity.toLowerCase()
  );

}


// --------------------------------------------------------
// PRICE
// --------------------------------------------------------

if (selectedPrice !== "All") {

  result = result.filter((card) => {

    const price = Number(
      card.current_value || 0
    );

    switch (selectedPrice) {

      case "under-1":
        return price < 1;

      case "1-5":
        return price >= 1 && price < 5;

      case "5-20":
        return price >= 5 && price < 20;

      case "20-50":
        return price >= 20 && price < 50;

      case "50-plus":
        return price >= 50;

      default:
        return true;

    }

  });

}


// --------------------------------------------------------
// SORT
// --------------------------------------------------------

result.sort((a, b) => {

  const nameA =
    String(a.name || "").toLowerCase();

  const nameB =
    String(b.name || "").toLowerCase();

  const priceA =
    Number(a.current_value || 0);

  const priceB =
    Number(b.current_value || 0);

  const rarityA =
    String(a.rarity || "").toLowerCase();

  const rarityB =
    String(b.rarity || "").toLowerCase();

  const setA =
    String(a.set || "").toLowerCase();

  const setB =
    String(b.set || "").toLowerCase();


  switch (sortBy) {

    case "name-desc":
      return nameB.localeCompare(nameA);

    case "price-high":
      return priceB - priceA;

    case "price-low":
      return priceA - priceB;

    case "rarity":
      return rarityA.localeCompare(rarityB);

    case "set":
      return setA.localeCompare(setB);

    case "name-asc":
    default:
      return nameA.localeCompare(nameB);

  }

});


return result;
```

}, [
collection,
searchTerm,
selectedSet,
selectedRarity,
selectedPrice,
sortBy
]);

// ==========================================================
// TOTAL CARDS
// ==========================================================

const totalCards = useMemo(() => {

```
return collection.reduce(
  (total, card) =>
    total +
    Number(card.qty || 0) +
    Number(card.qty_foil || 0),
  0
);
```

}, [collection]);

// ==========================================================
// UNIQUE CARDS
// ==========================================================

const uniqueCards =
collection.length;

// ==========================================================
// COLLECTION VALUE
// ==========================================================

const collectionValue = useMemo(() => {

```
return collection.reduce(
  (total, card) =>
    total +
    Number(
      card.current_value || 0
    ),
  0
);
```

}, [collection]);

// ==========================================================
// LOADING
// ==========================================================

if (loading) {

```
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
```

}

// ==========================================================
// ERROR
// ==========================================================

if (error) {

```
return (

  <main>

    <div className="error">

      <h1>
        MTG Collection
      </h1>

      <p>
        Unable to load collection.
      </p>

      <p>
        {error}
      </p>

    </div>

  </main>

);
```

}

// ==========================================================
// WEBSITE
// ==========================================================

return (

```
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
        ${collectionValue.toFixed(2)}
      </strong>

    </div>

  </section>


  {/* =====================================================
      SEARCH + FILTERS
      ===================================================== */}

  <section className="filters">

    {/* SEARCH */}

    <div className="filter-group search-group">

      <label htmlFor="search">
        Search
      </label>

      <input
        id="search"
        type="search"
        placeholder="Search cards..."
        value={searchTerm}
        onChange={(event) =>
          setSearchTerm(event.target.value)
        }
      />

    </div>


    {/* SET */}

    <div className="filter-group">

      <label htmlFor="set-filter">
        Set
      </label>

      <select
        id="set-filter"
        value={selectedSet}
        onChange={(event) =>
          setSelectedSet(event.target.value)
        }
      >

        {setOptions.map((set) => (

          <option
            key={set}
            value={set}
          >
            {set === "All"
              ? "All Sets"
              : set.toUpperCase()}
          </option>

        ))}

      </select>

    </div>


    {/* RARITY */}

    <div className="filter-group">

      <label htmlFor="rarity-filter">
        Rarity
      </label>

      <select
        id="rarity-filter"
        value={selectedRarity}
        onChange={(event) =>
          setSelectedRarity(event.target.value)
        }
      >

        {rarityOptions.map((rarity) => (

          <option
            key={rarity}
            value={rarity}
          >
            {rarity === "All"
              ? "All Rarities"
              : rarity.charAt(0).toUpperCase() +
                rarity.slice(1)}
          </option>

        ))}

      </select>

    </div>


    {/* PRICE */}

    <div className="filter-group">

      <label htmlFor="price-filter">
        Price
      </label>

      <select
        id="price-filter"
        value={selectedPrice}
        onChange={(event) =>
          setSelectedPrice(event.target.value)
        }
      >

        <option value="All">
          All Prices
        </option>

        <option value="under-1">
          Under $1
        </option>

        <option value="1-5">
          $1 – $5
        </option>

        <option value="5-20">
          $5 – $20
        </option>

        <option value="20-50">
          $20 – $50
        </option>

        <option value="50-plus">
          $50+
        </option>

      </select>

    </div>


    {/* SORT */}

    <div className="filter-group">

      <label htmlFor="sort">
        Sort
      </label>

      <select
        id="sort"
        value={sortBy}
        onChange={(event) =>
          setSortBy(event.target.value)
        }
      >

        <option value="name-asc">
          Name A–Z
        </option>

        <option value="name-desc">
          Name Z–A
        </option>

        <option value="price-high">
          Price: High to Low
        </option>

        <option value="price-low">
          Price: Low to High
        </option>

        <option value="rarity">
          Rarity
        </option>

        <option value="set">
          Set
        </option>

      </select>

    </div>

  </section>


  {/* =====================================================
      RESULTS SUMMARY
      ===================================================== */}

  <div className="results-summary">

    <span>
      Showing{" "}
      <strong>
        {filteredCollection.length}
      </strong>{" "}
      of{" "}
      <strong>
        {collection.length}
      </strong>{" "}
      unique cards
    </span>

  </div>


  {/* =====================================================
      COLLECTION
      ===================================================== */}

  <section className="collection">

    <div className="card-grid">

      {filteredCollection.map((card) => (

        <article
          className="card"
          key={card.id}
        >

          <CardImage
            card={card}
          />


          <div className="card-info">

            <h3>
              {card.name}
            </h3>


            <p>

              {card.set?.toUpperCase()}
              {" • #"}
              {card.card_no}

            </p>


            <div className="card-footer">

              <span>

                Qty:{" "}

                {Number(card.qty || 0) +
                  Number(
                    card.qty_foil || 0
                  )}

              </span>


              <strong>

                $
                {Number(
                  card.current_value || 0
                ).toFixed(2)}

              </strong>

            </div>

          </div>

        </article>

      ))}

    </div>


    {/* ===================================================
        NO RESULTS
        =================================================== */}

    {filteredCollection.length === 0 && (

      <div className="no-results">

        <h3>
          No cards found
        </h3>

        <p>
          Try changing your search or filters.
        </p>

      </div>

    )}

  </section>

</main>
```

);
}

export default App;
         
