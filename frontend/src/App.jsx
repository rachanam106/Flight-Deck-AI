
import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const suggestions = [
  "Show me our current sales pipeline",
  "Show me the top 10 deals by value",
  "What is our total revenue this quarter?",
  "Show me the monthly revenue trend",
  "How much billing is pending?",
  "Which customers have the highest overdue billing?",
];

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function askQuestion(value = question) {
    if (!value.trim() || loading) return;

    setMessages(prev => [...prev, { role: "user", text: value }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: value }),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Request failed");

      setMessages(prev => [...prev, { role: "assistant", result }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: "assistant",
        error: error.message
      }]);
    } finally {
      setLoading(false);
    }
  }

  function renderResult(result) {
    if (result.status !== "success") return <p>{result.message}</p>;

    const rows = result.data || [];
    const columns = rows.length ? Object.keys(rows[0]) : [];

    return (
      <div className="result">
        <div className="result-meta">
          Query ID: {result.recognized_query} · Confidence: {Math.round(result.confidence * 100)}%
        </div>

        {rows.length === 0 ? <p>No records found.</p> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>{columns.map(col => <th key={col}>{col.replaceAll("_", " ")}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i}>
                    {columns.map(col => (
                      <td key={col}>
                        {typeof row[col] === "number"
                          ? row[col].toLocaleString("en-IN")
                          : String(row[col] ?? "—")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="source-note">Source: Approved SQL query · Neon PostgreSQL</p>
      </div>
    );
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">FD</div>
          <div><strong>FLIGHT DECK</strong><small>Decision Intelligence</small></div>
        </div>
        <div className="side-label">WORKSPACE</div>
        <div className="nav-item active">✦ Business Assistant</div>
        <div className="nav-item">▤ Sales Intelligence</div>
        <div className="nav-item">▤ Revenue Intelligence</div>
        <div className="nav-item">▤ Billing Intelligence</div>
        <div className="sidebar-bottom">
          <span className="status-dot" /> Backend connected
          <small>Demo · Synthetic data</small>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <span>Business Assistant / Overview</span>
          <span className="environment">DEMO ENVIRONMENT</span>
        </header>

        <section className="content">
          <div className="welcome">
            <div className="eyebrow">INTELLIGENT BUSINESS QUERY PLATFORM</div>
            <h1>Good morning. <span>What would you like to know?</span></h1>
            <p>Ask questions about sales, revenue and billing. Flight Deck retrieves answers from approved business queries.</p>
          </div>

          {messages.length === 0 && (
            <div className="suggestions">
              <h3>Try asking</h3>
              <div className="suggestion-grid">
                {suggestions.map(item => (
                  <button className="suggestion" key={item} onClick={() => askQuestion(item)}>
                    <span>↗</span>{item}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="conversation">
            {messages.map((message, i) => (
              <div className={`message ${message.role}`} key={i}>
                <div className="avatar">{message.role === "user" ? "Y" : "FD"}</div>
                <div className="message-content">
                  {message.role === "user" ? <p>{message.text}</p>
                    : message.error ? <p className="error">{message.error}</p>
                    : renderResult(message.result)}
                </div>
              </div>
            ))}
            {loading && <div className="loading">Flight Deck is retrieving your data…</div>}
          </div>

          <form className="composer" onSubmit={e => { e.preventDefault(); askQuestion(); }}>
            <input
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="Ask about your sales, revenue or billing..."
            />
            <button disabled={loading || !question.trim()}>Ask Flight Deck ↑</button>
          </form>
          <div className="disclaimer">Answers are retrieved from approved SQL queries. Demo data is synthetic.</div>
        </section>
      </main>
    </div>
  );
}

export default App;
