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

```
return (
  <div className="card-image-placeholder">
    No image available
  </div>
);
```

}

return (

```
<div className="card-image-container">

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
        setShowBack(
          (current) => !current
        )
      }
    >
      {showBack ? "Front" : "Reverse"}
    </button>

  )}

</div>
```

);
}

/* ============================================================
APP
============================================================ */

function App() {

const [collection, setCollection] =
useState([]);

const [loading, setLoading] =
useState(true);

const [error, setError] =
useState(null);

const [searchTerm, setSearchTerm] =
useState("");

/* ==========================================================
LOAD COLLECTION
========================================================== */

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

/* ==========================================================
TOTAL CARDS
========================================================== */

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

/* ==========================================================
UNIQUE CARDS
========================================================== */

const uniqueCards =
collection.length;

/* ==========================================================
COLLECTION VALUE
========================================================== */

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

/* ==========================================================
SEARCH
========================================================== */

const filteredCollection = useMemo(() => {

```
const search =
  searchTerm
    .trim()
    .toLowerCase();

if (!search) {
  return collection;
}

return collection.filter((card) => {

  const name =
    String(card.name || "")
      .toLowerCase();

  const set =
    String(card.set || "")
      .toLowerCase();

  const setName =
    String(card.set_name || "")
      .toLowerCase();

  const cardNumber =
    String(card.card_no || "")
      .toLowerCase();

  const collectorNumber =
    String(card.collector_number || "")
      .toLowerCase();

  return (
    name.includes(search) ||
    set.includes(search) ||
    setName.includes(search) ||
    cardNumber.includes(search) ||
    collectorNumber.includes(search)
  );

});
```

}, [collection, searchTerm]);

/* ==========================================================
LOADING
========================================================== */

if (loading) {

```
return (

  <main>

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

/* ==========================================================
ERROR
========================================================== */

if (error) {

```
return (

  <main>

    <h1>
      MTG Collection
    </h1>

    <p>
      Unable to load collection.
    </p>

    <p>
      {error}
    </p>

  </main>

);
```

}

/* ==========================================================
WEBSITE
========================================================== */

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
      COLLECTION
      ===================================================== */}

  <section className="collection">

    <div className="collection-header">

      <div>

        <h2>
          Collection
        </h2>

        <p className="result-count">

          Showing{" "}
          {filteredCollection.length}
          {" of "}
          {collection.length}
          {" cards"}

        </p>

      </div>


      {/* =================================================
          SEARCH
          ================================================= */}

      <div className="search-container">

        <input
          type="search"
          className="search-input"
          placeholder="Search cards..."
          value={searchTerm}
          onChange={(event) =>
            setSearchTerm(
              event.target.value
            )
          }
          aria-label="Search collection"
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
        NO RESULTS
        =================================================== */}

    {filteredCollection.length === 0 ? (

      <div className="no-results">

        <h3>
          No cards found
        </h3>

        <p>
          Try a different card name, set or
          collector number.
        </p>

      </div>

    ) : (

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

    )}

  </section>

</main>
```

);

}

export default App;
