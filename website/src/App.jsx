import { useEffect, useMemo, useState } from "react";

function App() {
  const [collection, setCollection] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

useEffect(() => {
  fetch("./collection.json")
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

  if (loading) {
    return (
      <main>
        <h1>MTG Collection</h1>
        <p>Loading collection...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <h1>MTG Collection</h1>
        <p>Unable to load collection.</p>
        <p>{error}</p>
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
          <strong>{totalCards}</strong>
        </div>

        <div className="stat-card">
          <span>Unique Cards</span>
          <strong>{uniqueCards}</strong>
        </div>

        <div className="stat-card">
          <span>Collection Value</span>
          <strong>
            ${collectionValue.toFixed(2)}
          </strong>
        </div>

      </section>

      <section className="collection">

        <h2>Collection</h2>

        <div className="card-grid">

          {collection.map((card) => (

            <article
              className="card"
              key={card.id}
            >

              {card.image_url && (
                <img
                  src={card.image_url}
                  alt={card.name}
                />
              )}

              <div className="card-info">

                <h3>{card.name}</h3>

                <p>
                  {card.set?.toUpperCase()} • #
                  {card.card_no}
                </p>

                <div className="card-footer">

                  <span>
                    Qty:{" "}
                    {Number(card.qty || 0) +
                      Number(card.qty_foil || 0)}
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

      </section>
    </main>
  );
}

export default App;
