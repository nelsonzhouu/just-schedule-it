import { useState } from 'react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Clear previous response and errors
    setResponse('')
    setError('')

    // Validate input
    if (!message.trim()) {
      setError('Please enter a message')
      return
    }

    setLoading(true)

    try {
      // Send POST request to Flask backend
      // The /api prefix is automatically proxied to localhost:5000 by Vite
      const res = await axios.post('/api/message', {
        message: message
      })

      if (res.data.success) {
        setResponse(res.data.response)
      } else {
        setError(res.data.error || 'An error occurred')
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setError(
        err.response?.data?.error ||
        'Failed to connect to server. Make sure the Flask backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>JustScheduleIt</h1>
      <p className="subtitle">Manage your Google Calendar with natural language</p>

      <form onSubmit={handleSubmit} className="message-form">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message to send to the backend..."
          className="message-input"
          disabled={loading}
        />
        <button
          type="submit"
          className="submit-button"
          disabled={loading}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {response && (
        <div className="response-box">
          <strong>Response:</strong>
          <p>{response}</p>
        </div>
      )}

      <div className="info-box">
        <p><strong>Phase 1:</strong> Testing Flask ↔ React communication</p>
        <p>The backend will echo back whatever you send.</p>
      </div>
    </div>
  )
}

export default App
