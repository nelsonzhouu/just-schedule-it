/**
 * ChatMessage Component
 *
 * Displays a single message exchange in the chat history.
 * Shows the user's command and a conversational, friendly response.
 *
 * FEATURES:
 * - User message bubble (right-aligned, dark)
 * - Response bubble showing conversational message
 * - Timestamp
 * - Success/error styling
 *
 * PROPS:
 * - userMessage: The user's natural language command (string)
 * - response: Object with { message, result } from backend
 * - timestamp: When the message was sent (Date)
 * - isError: Whether this was an error response (boolean)
 */

import './ChatMessage.css'

/**
 * Format a Date object into a readable time string.
 * Example: "2:34 PM"
 *
 * @param {Date} date - The date to format
 * @returns {string} Formatted time string
 */
function formatTime(date) {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

/**
 * @param {Object} props
 * @param {string} props.userMessage - User's command
 * @param {Object} props.response - Parsed response data
 * @param {Date} props.timestamp - Message timestamp
 * @param {boolean} props.isError - Whether this is an error
 */
function ChatMessage({ userMessage, response, timestamp, isError }) {
  return (
    <div className="chat-message">
      {/* ==================== User Message Bubble ==================== */}
      {/* Right-aligned bubble showing what the user typed */}
      <div className="message-user">
        <div className="message-bubble message-bubble-user">
          <p className="message-text">{userMessage}</p>
          <span className="message-time">{formatTime(timestamp)}</span>
        </div>
      </div>

      {/* ==================== Response Bubble ==================== */}
      {/* Left-aligned bubble showing conversational response */}
      <div className="message-response">
        <div className={`message-bubble message-bubble-response ${isError ? 'message-bubble-error' : ''}`}>
          {/* Show the conversational message */}
          <div className="response-message">
            {/* Display the conversational message with line breaks preserved */}
            <p style={{ whiteSpace: 'pre-line' }}>
              {isError ? response.error : response.message}
            </p>
          </div>

          <span className="message-time">{formatTime(timestamp)}</span>
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
