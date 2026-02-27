/**
 * ChatMessage Component
 *
 * Displays a single message exchange in the chat history.
 * Shows both the user's command and the parsed response from the backend.
 *
 * FEATURES:
 * - User message bubble (right-aligned, blue)
 * - Response bubble (left-aligned, gray or red for errors)
 * - Timestamp
 * - Formatted display of parsed command data
 * - Error handling for failed parses
 *
 * PROPS:
 * - userMessage: The user's natural language command (string)
 * - response: The parsed data from Groq API (object)
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
      {/* Left-aligned bubble showing the parsed result */}
      <div className="message-response">
        <div className={`message-bubble message-bubble-response ${isError ? 'message-bubble-error' : ''}`}>
          {/* If error, show error message */}
          {isError ? (
            <div className="response-error">
              <strong>Error:</strong>
              <p>{response.error || 'An error occurred'}</p>
            </div>
          ) : (
            /* Otherwise, show parsed command data */
            <div className="response-data">
              {/* Action type (create, delete, move, list) */}
              {response.action && (
                <div className="response-field">
                  <span className="field-label">Action:</span>
                  <span className="field-value action-badge">{response.action}</span>
                </div>
              )}

              {/* Event title (if provided) */}
              {response.title && (
                <div className="response-field">
                  <span className="field-label">Title:</span>
                  <span className="field-value">{response.title}</span>
                </div>
              )}

              {/* Date (if provided) */}
              {response.date && (
                <div className="response-field">
                  <span className="field-label">Date:</span>
                  <span className="field-value">{response.date}</span>
                </div>
              )}

              {/* Time (if provided) */}
              {response.time && (
                <div className="response-field">
                  <span className="field-label">Time:</span>
                  <span className="field-value">{response.time}</span>
                </div>
              )}

              {/* End time (for move operations with new time) */}
              {response.end_time && (
                <div className="response-field">
                  <span className="field-label">End Time:</span>
                  <span className="field-value">{response.end_time}</span>
                </div>
              )}

              {/* New date (for move operations) */}
              {response.new_date && (
                <div className="response-field">
                  <span className="field-label">New Date:</span>
                  <span className="field-value">{response.new_date}</span>
                </div>
              )}

              {/* New time (for move operations) */}
              {response.new_time && (
                <div className="response-field">
                  <span className="field-label">New Time:</span>
                  <span className="field-value">{response.new_time}</span>
                </div>
              )}

              {/* Confidence score */}
              {response.confidence && (
                <div className="response-field">
                  <span className="field-label">Confidence:</span>
                  <span className="field-value confidence-score">
                    {(response.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}

              {/* Note about Phase 3C */}
              <p className="response-note">
                <em>Command parsed successfully! Execution coming in Phase 3C.</em>
              </p>
            </div>
          )}

          <span className="message-time">{formatTime(timestamp)}</span>
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
