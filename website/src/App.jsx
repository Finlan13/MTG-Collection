import { useEffect, useMemo, useState } from "react";

function App() {
  const [collection, setCollection] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState("");
  const [setFilter, setSetFilter] = useState("All Sets");
  const [rarityFilter, setRarityFilter] = useState("All Rarities");
  const [foilFilter, setFoilFilter] = useState("All Cards");
  const [sortBy, setSortBy] = useState("name");

  useEffect(() => {
    fetch("/MTG-Collection/collection.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Unable to load collection data.");
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
  }, []);

  const sets = useMemo(() => {
    return [
      "All Sets",
      ...Array.from(
        new Set(
          collection
            .map((card) => card.set_name || card.set)
            .filter(Boolean)
        )
      ).sort(),
    ];
  }, [collection]);

  const rarities = useMemo(() => {
    return [
      "All Rarities",
      ...Array.from(
        new Set(
          collection
            .map((card) => card.rarity)
            .filter(Boolean)
        )
      ).sort(),
    ];
  }, [collection]);

  const filteredCollection = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();

    const filtered = collection.filter((card) => {
      const cardName = String(card.name || "").toLowerCase();
      const setName = String(
        card.set_name || card.set || ""
      ).toLowerCase();
      const cardNumber = String(card.card_no || "").toLowerCase();
      const artist = String(card.artist || "").toLowerCase();

      const matchesSearch =
        !searchTerm ||
        cardName.includes(searchTerm) ||
        setName.includes(searchTerm) ||
        cardNumber.includes(searchTerm) ||
        artist.includes(searchTerm);

      const matchesSet =
        setFilter === "All Sets" ||
        (card.set_name || card.set) === setFilter;

      const matchesRarity =
        rarityFilter === "All Rarities" ||
        card.rarity === rarityFilter;

      const nonFoilQty = Number(card.qty || 0);
      const foilQty = Number(card.qty_foil || 0);

      const matchesFoil =
        foilFilter === "All Cards" ||
        (foilFilter === "Foil" && foilQty > 0) ||
        (foilFilter === "Non-Foil" && nonFoilQty > 0);

      return (
        matchesSearch &&
        matchesSet &&
        matchesRarity &&
        matchesFoil
      );
    });

    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "price-high":
          return (
            Number(b.current_value || 0) -
            Number(a.current_value || 0)
          );

        case "price-low":
          return (
            Number(a.current_value || 0) -
            Number(b.current_value || 0)
          );

        case "quantity":
          return (
            Number(b.qty || 0) +
            Number(b.qty_foil || 0) -
            (Number(a.qty || 0) +
              Number(a.qty_foil || 0))
          );

        case "set":
          return String(
            a.set_name || a.set || ""
          ).localeCompare(
            String(b.set_name || b.set || "")
          );

        case "name":
        default:
          return String(a.name || "").localeCompare(
            String(b.name || "")
          );
      }
    });
  }, [
    collection,
    search,
    setFilter,
    rarityFilter,
    foilFilter,
    sortBy,
  ]);

  const totalCards = useMemo(() => {
    return collection.reduce(
      (total, card) =>
        total +
        Number(card.qty || 0) +
        Number(card.qty_foil || 0),
      0
    );
  }, [collection]);

  const uniqueCards = collection.length;

  const collectionValue = useMemo(() => {
    return collection.reduce(
      (total, card) =>
        total + Number(card.current_value || 0),
      0
    );
  }, [collection]);

  const clearFilters = () => {
    setSearch("");
    setSetFilter("All Sets");
    setRarityFilter("All Rarities");
    setFoilFilter("All Cards");
    setSortBy("name");
  };

  if (loading) {
    return (
      <main className="page">
        <div className="loading">
          <h1>MTG Collection</h1>
          <p>Loading collection...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <div className="error">
          <h1>MTG Collection</h1>
          <p>Unable to load collection.</p>
          <p>{error}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="page">

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
          <strong>{totalCards.toLocaleString()}</strong>
        </div>

        <div className="stat-card">
          <span>Unique Cards</span>
          <strong>{uniqueCards.toLocaleString()}</strong>
        </div>

        <div className="stat-card">
          <span>Collection Value</span>
          <strong>
            ${collectionValue.toFixed(2)}
          </strong>
        </div>

      </section>

      <section className="controls">

        <div className="search-container">
          <input
            type="text"
            placeholder="Search cards, sets, numbers or artists..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="filters">

          <select
            value={setFilter}
            onChange={(e) => setSetFilter(e.target.value)}
          >
            {sets.map((set) => (
              <option key={set} value={set}>
                {set}
              </option>
            ))}
          </select>

          <select
            value={rarityFilter}
            onChange={(e) =>
              setRarityFilter(e.target.value)
            }
          >
            {rarities.map((rarity) => (
              <option key={rarity} value={rarity}>
                {rarity === "All Rarities"
                  ? rarity
                  : rarity.charAt(0).toUpperCase() +
                    rarity.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={foilFilter}
            onChange={(e) =>
              setFoilFilter(e.target.value)
            }
          >
            <option value="All Cards">
              All Cards
            </option>
            <option value="Non-Foil">
              Non-Foil
            </option>
            <option value="Foil">
              Foil
            </option>
          </select>

          <select
            value={sortBy}
            onChange={(e) =>
              setSortBy(e.target.value)
            }
          >
            <option value="name">
              Sort: Name
            </option>
            <option value="set">
              Sort: Set
            </option>
            <option value="price-high">
              Sort: Value (High → Low)
            </option>
            <option value="price-low">
              Sort: Value (Low → High)
            </option>
            <option value="quantity">
              Sort: Quantity
            </option>
          </select>

          <button
            className="clear-button"
            onClick={clearFilters}
          >
            Clear
          </button>

        </div>

        <div className="result-count">
          Showing{" "}
          <strong>
            {filteredCollection.length.toLocaleString()}
          </strong>{" "}
          of{" "}
          <strong>
            {collection.length.toLocaleString()}
          </strong>{" "}
          unique cards
        </div>

      </section>

      <section className="collection">

        <div className="collection-header">
          <h2>Collection</h2>
        </div>

        {filteredCollection.length === 0 ? (
          <div className="no-results">
            <h3>No cards found</h3>
            <p>
              Try changing your search or filters.
            </p>
          </div>
        ) : (
          <div className="card-grid">

            {filteredCollection.map((card) => {

              const nonFoilQty = Number(card.qty || 0);
              const foilQty = Number(
                card.qty_foil || 0
              );

              const totalQty =
                nonFoilQty + foilQty;

              return (
                <article
                  className="card"
                  key={card.id}
                >

                  {card.image_url && (
                    <img
                      src={card.image_url}
                      alt={card.name}
                      loading="lazy"
                    />
                  )}

                  <div className="card-info">

                    <h3>{card.name}</h3>

                    <p className="card-set">
                      {(
                        card.set_name ||
                        card.set ||
                        ""
                      )}
                      {" • "}
                      #{card.card_no}
                    </p>

                    <div className="quantity">

                      {nonFoilQty > 0 && (
                        <span>
                          Non-Foil: {nonFoilQty}
                        </span>
                      )}

                      {foilQty > 0 && (
                        <span className="foil">
                          Foil: {foilQty}
                        </span>
                      )}

                    </div>

                    <div className="card-footer">

                      <span>
                        Qty: {totalQty}
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
              );
            })}

          </div>
        )}

      </section>

    </main>
  );
}

export default App;
