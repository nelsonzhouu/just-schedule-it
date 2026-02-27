/**
 * Dashboard Component
 *
 * Main application page for authenticated users.
 *
 * FEATURES:
 * - Header with user profile and logout button
 * - Calendar placeholder (Phase 3C will implement real Google Calendar integration)
 * - Chat interface for natural language commands
 * - Session-based chat history (stored in React state, clears on refresh)
 *
 * LAYOUT:
 * - Header at top (fixed height)
 * - Two-column layout below header:
 *   - Left: Calendar view (placeholder for now)
 *   - Right: Chat interface with message history and input
 *
 * DATA FLOW:
 * 1. Component mounts → fetch user data from /api/auth/user
 * 2. User types command → MessageInput sends to /api/message
 * 3. Response comes back → add to chat history state
 * 4. ChatMessage components render the history
 * 5. On page refresh → history clears (session-based, not persisted)
 */

import { useState, useEffect, useRef } from 'react'
import { checkAuth, logout } from '../utils/auth'
import api from '../utils/api'
import MessageInput from '../components/MessageInput'
import ChatMessage from '../components/ChatMessage'
import './Dashboard.css'

function Dashboard() {
  // ==================== State Management ====================

  // User profile data (fetched from /api/auth/user)
  const [user, setUser] = useState(null)

  // Loading state for initial user fetch
  const [loading, setLoading] = useState(true)

  // Chat history - array of message objects
  // Each message has: { id, userMessage, response, timestamp, isError }
  // SESSION-BASED: Clears when page refreshes (not stored in database)
  const [chatHistory, setChatHistory] = useState([])

  // Ref to chat container for auto-scrolling to bottom
  const chatEndRef = useRef(null)

  // Track if profile picture failed to load (use fallback initial)
  const [imageError, setImageError] = useState(false)

  // ==================== Effects ====================

  // Fetch user data when component mounts
  useEffect(() => {
    async function fetchUser() {
      // checkAuth() calls /api/auth/user and returns user object or null
      const userData = await checkAuth()

      if (userData) {
        setUser(userData)
      }

      setLoading(false)
    }

    fetchUser()
  }, []) // Empty dependency array = run once on mount

  // Auto-scroll to bottom when chat history changes
  useEffect(() => {
    // Scroll to the bottom element smoothly
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory]) // Run whenever chatHistory changes

  // ==================== Helper Functions ====================

  /**
   * Get the first letter of the user's name for the avatar fallback.
   *
   * @returns {string} First letter of the user's name, uppercased
   */
  const getUserInitial = () => {
    if (!user || !user.name) return '?'
    return user.name.charAt(0).toUpperCase()
  }

  // ==================== Event Handlers ====================

  /**
   * Handle new message submission from MessageInput component.
   *
   * FLOW:
   * 1. MessageInput sends message to /api/message
   * 2. Backend parses with Groq API
   * 3. Response comes back with parsed data
   * 4. Add both user message and response to chat history
   *
   * @param {string} message - The user's natural language command
   * @param {Object} response - The parsed response from backend
   * @param {boolean} isError - Whether this was an error response
   */
  const handleMessageSent = (message, response, isError = false) => {
    // Create a new message object
    const newMessage = {
      id: Date.now(), // Simple unique ID (timestamp)
      userMessage: message,
      response: response,
      timestamp: new Date(),
      isError: isError
    }

    // Add to chat history (immutable update pattern)
    setChatHistory(prev => [...prev, newMessage])
  }

  /**
   * Handle logout button click.
   * Calls logout() from auth utils which clears cookie and redirects to homepage.
   */
  const handleLogout = () => {
    logout()
  }

  // ==================== Render ====================

  // Show loading state while fetching user data
  if (loading) {
    return (
      <div className="dashboard-loading">
        <p>Loading...</p>
      </div>
    )
  }

  // User data should always exist here (ProtectedRoute ensures auth)
  // But add fallback just in case
  if (!user) {
    return (
      <div className="dashboard-loading">
        <p>Unable to load user data</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      {/* ==================== Header ==================== */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1 className="dashboard-title">JustScheduleIt</h1>
          <span className="header-tagline">AI-powered calendar assistant</span>
        </div>

        <div className="header-right">
          {/* User profile info */}
          <div className="user-info">
            {/* User profile picture from Google, or fallback to initial circle */}
            {user.picture && !imageError ? (
              <img
                src={user.picture}
                alt={user.name}
                className="user-avatar"
                onError={() => setImageError(true)} // Show fallback if image fails to load
              />
            ) : (
              // Fallback: Show user's first initial in a colored circle
              <div className="user-avatar-fallback">
                {getUserInitial()}
              </div>
            )}

            {/* User name */}
            <span className="user-name">{user.name}</span>
          </div>

          {/* Logout button */}
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      {/* ==================== Main Content Area ==================== */}
      <div className="dashboard-content">
        {/* Left Column: Calendar View */}
        <div className="calendar-section">
          <h2 className="section-title">Your Calendar</h2>

          {/* Placeholder for now - Phase 3C will integrate Google Calendar */}
          <div className="calendar-placeholder">
            <p>📅 Calendar view coming in Phase 3C</p>
            <p className="placeholder-note">
              This will display your Google Calendar with events you can manage
              using natural language commands.
            </p>
          </div>
        </div>

        {/* Right Column: Chat Interface */}
        <div className="chat-section">
          <h2 className="section-title">Chat</h2>

          {/* Chat history container - scrollable */}
          <div className="chat-history">
            {/* Show welcome message if no chat history yet */}
            {chatHistory.length === 0 ? (
              <div className="welcome-message">
                <p>👋 Welcome! Try a command like:</p>
                <ul>
                  <li>"Schedule a meeting tomorrow at 3pm"</li>
                  <li>"Cancel my dentist appointment Friday"</li>
                  <li>"Move my 2pm meeting to Thursday at 4pm"</li>
                  <li>"What do I have on Friday?"</li>
                </ul>
                <p className="note">
                  Note: Commands are parsed but not executed yet (Phase 3C).
                  Chat history clears when you refresh the page.
                </p>
              </div>
            ) : (
              // Render all chat messages
              <>
                {chatHistory.map(msg => (
                  <ChatMessage
                    key={msg.id}
                    userMessage={msg.userMessage}
                    response={msg.response}
                    timestamp={msg.timestamp}
                    isError={msg.isError}
                  />
                ))}

                {/* Invisible element to scroll to */}
                <div ref={chatEndRef} />
              </>
            )}
          </div>

          {/* Message input at bottom */}
          <MessageInput onMessageSent={handleMessageSent} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard
