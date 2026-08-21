import { useState, useEffect } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

interface ChatResponse {
  answer: string
}

function App() {
  const [message, setMessage] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
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

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      })

      const data: ChatResponse = await res.json()
      setAnswer(data.answer)
    } catch (err) {
      setAnswer('Something went wrong. Is the backend running?')
      console.error('Chat request failed:', err)
    } finally {
      setLoading(false)
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

      <main>
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
        </section>

        <section className="section">
          <h2>Courses</h2>
          <p>Coming soon...</p>
        </section>

        <section className="section">
          <h2>Memory</h2>
          <p>Coming soon...</p>
        </section>
      </main>
    </div>
  )
}

export default App
