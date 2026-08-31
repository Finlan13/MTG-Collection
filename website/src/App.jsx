import { useEffect, useMemo, useState } from "react";

function CardImage({ card }) {
  const [showBack, setShowBack] = useState(false);

  const frontImage = card.image_url;
  const backImage = card.back_image_url;

  const currentImage =
    showBack && backImage ? backImage : frontImage;

  if (!currentImage) {
    return (
      <div className="image-placeholder">
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
            setShowBack(function (current) {
              return !current;
            })
          }
        >
          {showBack ? "Front" : "Reverse"}
        </button>
      )}
    </div>
  );
}

function App() {
  const [collection, setCollection] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSet, setSelectedSet] = useState("All");
  const [selectedRarity, setSelectedRarity] = useState("All");
  const [priceFilter, setPriceFilter] = useState("All");
  const [sortBy, setSortBy] = useState("name-asc");

  useEffect(function () {
    const collectionUrl =
      import.meta.env.BASE_URL + "collection.json";

    fetch(collectionUrl)
      .then(function (response) {
        if (!response.ok) {
          throw new Error(
            "Unable to load collection data."
          );
        }

        return response.json();
      })
      .then(function (data) {
        setCollection(data);
        setLoading(false);
      })
      .catch(function (err) {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const totalCards = useMemo(function () {
    return collection.reduce(
      function (total, card) {
        return (
          total +
          Number(card.qty || 0) +
          Number(card.qty_foil || 0)
        );
      },
      0
    );
  }, [collection]);

  const uniqueCards = collection.length;

  const collectionValue = useMemo(function () {
    return collection.reduce(
      function (total, card) {
        return (
          total +
          Number(card.current_value || 0)
        );
      },
      0
    );
  }, [collection]);

  const sets = useMemo(function () {
    const values = collection
      .map(function (card) {
        return card.set_name || card.set;
      })
      .filter(Boolean);

    return [
      "All",
      ...Array.from(new Set(values)).sort(
        function (a, b) {
          return a.localeCompare(b);
        }
      ),
    ];
  }, [collection]);

  const rarities = useMemo(function () {
    const values = collection
      .map(function (card) {
        return card.rarity;
      })
      .filter(Boolean);

    return [
      "All",
      ...Array.from(new Set(values)).sort(
        function (a, b) {
          return a.localeCompare(b);
        }
      ),
    ];
  }, [collection]);

  const filteredCollection = useMemo(
    function () {
      let result = collection.filter(
        function (card) {
          const name = String(
            card.name || ""
          ).toLowerCase();

          const setName = String(
            card.set_name ||
            card.set ||
            ""
          );

          const rarity = String(
            card.rarity || ""
          );

          const price = Number(
            card.current_value || 0
          );

          const matchesSearch =
            name.includes(
              searchTerm.toLowerCase()
            );

          const matchesSet =
            selectedSet === "All" ||
            setName === selectedSet;

          const matchesRarity =
            selectedRarity === "All" ||
            rarity === selectedRarity;

          let matchesPrice = true;

          if (priceFilter === "under1") {
            matchesPrice = price < 1;
          }

          if (priceFilter === "1to5") {
            matchesPrice =
              price >= 1 && price < 5;
          }

          if (priceFilter === "5to20") {
            matchesPrice =
              price >= 5 && price < 20;
          }

          if (priceFilter === "20plus") {
            matchesPrice = price >= 20;
          }

          return (
            matchesSearch &&
            matchesSet &&
            matchesRarity &&
            matchesPrice
          );
        }
      );

      result = [...result].sort(
        function (a, b) {
          const priceA = Number(
            a.current_value || 0
          );

          const priceB = Number(
            b.current_value || 0
          );

          const nameA = String(
            a.name || ""
          );

          const nameB = String(
            b.name || ""
          );

          const setA = String(
            a.set_name ||
            a.set ||
            ""
          );

          const setB = String(
            b.set_name ||
            b.set ||
            ""
          );

          const rarityA = String(
            a.rarity || ""
          );

          const rarityB = String(
            b.rarity || ""
          );

          switch (sortBy) {
            case "name-desc":
              return nameB.localeCompare(nameA);

            case "price-high":
              return priceB - priceA;

            case "price-low":
              return priceA - priceB;

            case "set-asc":
              return setA.localeCompare(setB);

            case "rarity-asc":
              return rarityA.localeCompare(
                rarityB
              );

            case "name-asc":
            default:
              return nameA.localeCompare(
                nameB
              );
          }
        }
      );

      return result;
    },
    [
      collection,
      searchTerm,
      selectedSet,
      selectedRarity,
      priceFilter,
      sortBy,
    ]
  );

  if (loading) {
    return (
      <main className="loading">
        <p>Loading collection...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <div className="error">
          <h1>
            Unable to load collection.
          </h1>

          <p>{error}</p>
        </div>
      </main>
    );
  }

  return (
    <main>
      <header className="header">
        <div>
          <h1>MTG Collection</h1>

          <p>
            My Magic: The Gathering collection
          </p>
        </div>
      </header>

      <section className="stats">
        <div className="stat-card">
          <span>Total Cards</span>

          <strong>
            {totalCards}
          </strong>
        </div>

        <div className="stat-card">
          <span>Unique Cards</span>

          <strong>
            {uniqueCards}
          </strong>
        </div>

        <div className="stat-card">
          <span>Collection Value</span>

          <strong>
            ${collectionValue.toFixed(2)}
          </strong>
        </div>
      </section>

      <section className="filters">

        <div className="search-box">
          <label htmlFor="search">
            Search cards
          </label>

          <input
            id="search"
            type="text"
            placeholder="Search by card name..."
            value={searchTerm}
            onChange={function (event) {
              setSearchTerm(
                event.target.value
              );
            }}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="set">
            Set
          </label>

          <select
            id="set"
            value={selectedSet}
            onChange={function (event) {
              setSelectedSet(
                event.target.value
              );
            }}
          >
            {sets.map(function (set) {
              return (
                <option
                  key={set}
                  value={set}
                >
                  {set}
                </option>
              );
            })}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="rarity">
            Rarity
          </label>

          <select
            id="rarity"
            value={selectedRarity}
            onChange={function (event) {
              setSelectedRarity(
                event.target.value
              );
            }}
          >
            {rarities.map(
              function (rarity) {
                return (
                  <option
                    key={rarity}
                    value={rarity}
                  >
                    {rarity === "All"
                      ? "All rarities"
                      : rarity
                          .charAt(0)
                          .toUpperCase() +
                        rarity.slice(1)}
                  </option>
                );
              }
            )}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="price">
            Price
          </label>

          <select
            id="price"
            value={priceFilter}
            onChange={function (event) {
              setPriceFilter(
                event.target.value
              );
            }}
          >
            <option value="All">
              All prices
            </option>

            <option value="under1">
              Under $1
            </option>

            <option value="1to5">
              $1 – $5
            </option>

            <option value="5to20">
              $5 – $20
            </option>

            <option value="20plus">
              $20+
            </option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="sort">
            Sort
          </label>

          <select
            id="sort"
            value={sortBy}
            onChange={function (event) {
              setSortBy(
                event.target.value
              );
            }}
          >
            <option value="name-asc">
              Name A–Z
            </option>

            <option value="name-desc">
              Name Z–A
            </option>

            <option value="price-high">
              Price high–low
            </option>

            <option value="price-low">
              Price low–high
            </option>

            <option value="set-asc">
              Set A–Z
            </option>

            <option value="rarity-asc">
              Rarity A–Z
            </option>
          </select>
        </div>

      </section>

      <div className="results-summary">
        Showing {filteredCollection.length} of{" "}
        {collection.length} cards
      </div>

      <section className="collection">

        <h2>Collection</h2>

        {filteredCollection.length === 0 ? (

          <div className="no-results">

            <h3>No cards found</h3>

            <p>
              Try changing your search or
              filters.
            </p>

          </div>

        ) : (

          <div className="card-grid">

            {filteredCollection.map(
              function (card) {

                return (

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
                        {(
                          card.set_name ||
                          card.set ||
                          ""
                        ).toUpperCase()}

                        {" • #"}

                        {card.card_no}
                      </p>

                      <div className="card-footer">

                        <span>
                          Qty:{" "}
                          {Number(
                            card.qty || 0
                          ) +
                            Number(
                              card.qty_foil ||
                              0
                            )}
                        </span>

                        <strong>
                          $
                          {Number(
                            card.current_value ||
                              0
                          ).toFixed(2)}
                        </strong>

                      </div>

                    </div>

                  </article>

                );
              }
            )}

          </div>

        )}

      </section>

    </main>
  );
}

export default App;
