import { useState, useEffect } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

interface ChatResponse {
  answer: string
  sources: {
    document: string
    score: number
  }[]
}

interface SearchResponse {
  results: {
    document: string
    text: string
    score: number
  }[]
}

type Tab = 'chat' | 'search' | 'courses' | 'memory'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat')

  const [message, setMessage] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<ChatResponse['sources']>([])
  const [loading, setLoading] = useState(false)

  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResponse['results']>([])
  const [searching, setSearching] = useState(false)

  const [health, setHealth] = useState<string | null>(null)

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`)
      const data = await res.json()
      setHealth(data.status)
    } catch (err) {
      setHealth('offline')
      console.error('Health check failed:', err)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    setLoading(true)
    setAnswer('')
    setSources([])

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      })

      const data: ChatResponse = await res.json()
      setAnswer(data.answer)
      setSources(data.sources ?? [])
    } catch (err) {
      setAnswer('Something went wrong. Is the backend running?')
      setSources([])
      console.error('Chat request failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const runSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setSearching(true)
    setSearchResults([])

    try {
      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })

      const data: SearchResponse = await res.json()
      setSearchResults(data.results)
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  useEffect(() => {
    try {
      checkHealth()
    } catch (err) {
      console.error('useEffect error:', err)
    }
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>AI Learning Assistant</h1>
        <span className="health">Backend: {health ?? 'checking...'}</span>
      </header>

      <nav className="tabs">
        {(['chat', 'search', 'courses', 'memory'] as Tab[]).map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? 'tab active' : 'tab'}
            onClick={() => setActiveTab(tab)}
          >
            {tab[0].toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      <main>
        {activeTab === 'chat' && (
          <section className="section">
            <h2>Chat</h2>
            <form onSubmit={sendMessage} className="chat-form">
              <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message..."
                className="chat-input"
              />
              <button type="submit" disabled={loading} className="chat-button">
                {loading ? 'Sending...' : 'Send'}
              </button>
            </form>

            {answer && <p className="answer">{answer}</p>}

            {sources.length > 0 && (
              <div className="sources">
                <h4>Sources</h4>
                <ul>
                  {sources.map((source, idx) => (
                    <li key={idx}>
                      {source.document} — score: {source.score.toFixed(4)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {activeTab === 'search' && (
          <section className="section">
            <h2>Search Knowledge Base</h2>
            <form onSubmit={runSearch} className="chat-form">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What is React?"
                className="chat-input"
              />
              <button type="submit" disabled={searching} className="chat-button">
                {searching ? 'Searching...' : 'Search'}
              </button>
            </form>

            {searchResults.length > 0 && (
              <div className="results">
                <h3>Retrieved chunks</h3>
                {searchResults.map((result, idx) => (
                  <div key={idx} className="result-card">
                    <p className="result-meta">
                      <strong>{result.document}</strong> — score: {result.score.toFixed(4)}
                    </p>
                    <p className="result-text">{result.text}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {activeTab === 'courses' && (
          <section className="section">
            <h2>Courses</h2>
            <p>Coming soon...</p>
          </section>
        )}

        {activeTab === 'memory' && (
          <section className="section">
            <h2>Memory</h2>
            <p>Coming soon...</p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
