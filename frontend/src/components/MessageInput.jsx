/**
 * MessageInput Component
 *
 * Reusable input component for sending natural language commands to the backend.
 *
 * FEATURES:
 * - Text input for user commands
 * - Submit button (or press Enter)
 * - Loading state while waiting for backend response
 * - Input validation (no empty messages)
 * - Clears input after successful send
 *
 * PROPS:
 * - onMessageSent: Callback function called when response is received
 *   Signature: (message: string, response: object, isError: boolean) => void
 *
 * DATA FLOW:
 * 1. User types command and submits
 * 2. Component calls /api/message with the command
 * 3. Backend parses with Groq API and returns structured JSON
 * 4. Component calls onMessageSent with message and response
 * 5. Parent (Dashboard) adds to chat history
 */

import { useState } from 'react'
import api from '../utils/api'
import './MessageInput.css'

/**
 * @param {Object} props
 * @param {Function} props.onMessageSent - Callback when message is sent and response received
 */
function MessageInput({ onMessageSent }) {
  // ==================== State Management ====================

  // Current message being typed
  const [message, setMessage] = useState('')

  // Loading state while waiting for backend response
  const [isLoading, setIsLoading] = useState(false)

  // ==================== Event Handlers ====================

  /**
   * Handle form submission.
   *
   * FLOW:
   * 1. Prevent default form submission (no page reload)
   * 2. Validate input (no empty messages)
   * 3. Set loading state
   * 4. Call /api/message endpoint
   * 5. Pass response to parent via onMessageSent callback
   * 6. Clear input on success
   * 7. Handle errors gracefully
   *
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault() // Prevent page reload

    // Validate input - don't send empty messages
    if (!message.trim()) {
      return
    }

    // Store message before clearing input
    const currentMessage = message

    // Set loading state and clear input immediately for better UX
    // User sees input clear right away, feels more responsive
    setIsLoading(true)
    setMessage('') // Clear input immediately

    try {
      // Call the protected /api/message endpoint
      // This is where the natural language parsing happens with Groq API
      const response = await api.post('/message', {
        message: currentMessage
      })

      // Check if backend returned success
      if (response.data.success) {
        // Call parent callback with successful response
        // Parent (Dashboard) will add this to chat history
        onMessageSent(currentMessage, response.data.data, false)
      } else {
        // Backend returned error in response
        // Still show in chat but mark as error
        onMessageSent(
          currentMessage,
          { error: response.data.error || 'An error occurred' },
          true
        )
      }
    } catch (error) {
      // Network error or other exception
      console.error('Error sending message:', error)

      // Show error in chat
      onMessageSent(
        currentMessage,
        {
          error: error.response?.data?.error ||
                 'Failed to send message. Please try again.'
        },
        true
      )
    } finally {
      // Always stop loading state when request completes
      setIsLoading(false)
    }
  }

  // ==================== Render ====================

  return (
    <form onSubmit={handleSubmit} className="message-input-form">
      {/* Text input for command */}
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a command... (e.g., 'schedule meeting tomorrow at 3pm')"
        className="message-input-field"
        disabled={isLoading} // Disable input while loading
        autoFocus // Auto-focus for better UX
      />

      {/* Submit button */}
      <button
        type="submit"
        className="message-input-submit"
        disabled={isLoading || !message.trim()} // Disable if loading or empty
      >
        {isLoading ? 'Sending...' : 'Send'}
      </button>
    </form>
  )
}

export default MessageInput
