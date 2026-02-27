/**
 * Main App Component
 *
 * Sets up routing for the entire application.
 *
 * ROUTES:
 * - / (HomePage): Login page for unauthenticated users
 * - /dashboard (Dashboard): Main app page for authenticated users (protected)
 *
 * AUTHENTICATION FLOW:
 * 1. User visits / and sees "Login with Google" button
 * 2. Clicks button → redirects to backend /api/auth/login
 * 3. Backend redirects to Google OAuth consent screen
 * 4. User grants permissions → Google redirects back to backend callback
 * 5. Backend sets httpOnly JWT cookie → redirects to /dashboard
 * 6. ProtectedRoute checks authentication before showing Dashboard
 *
 * WHY ProtectedRoute:
 * - Prevents unauthorized users from accessing /dashboard
 * - Redirects to / if not logged in
 * - Only one place to handle auth logic (reusable)
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { checkAuth } from './utils/auth'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'

/**
 * ProtectedRoute Component
 *
 * Wrapper for routes that require authentication.
 * Checks if user is logged in before rendering the protected component.
 *
 * HOW IT WORKS:
 * 1. On mount, calls checkAuth() to verify the JWT cookie
 * 2. While checking, shows "Loading..." (prevents flash of wrong content)
 * 3. If authenticated, renders the children (Dashboard)
 * 4. If not authenticated, redirects to / (HomePage)
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - The protected component to render if authenticated
 */
function ProtectedRoute({ children }) {
  // Track authentication state
  // null = still checking, true = authenticated, false = not authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(null)

  // Check authentication when component mounts
  useEffect(() => {
    async function verify() {
      // Call the auth utility to check if user is logged in
      // This makes a request to /api/auth/user with the httpOnly cookie
      const user = await checkAuth()

      // If we got a user object back, they're authenticated
      // If we got null, they're not logged in
      setIsAuthenticated(user !== null)
    }

    verify()
  }, []) // Empty array means this only runs once when component mounts

  // Still checking authentication - show loading state
  // This prevents a flash of the wrong page while we check
  if (isAuthenticated === null) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '20px'
      }}>
        Loading...
      </div>
    )
  }

  // Not authenticated - redirect to login page
  if (!isAuthenticated) {
    return <Navigate to="/" replace />
  }

  // Authenticated - render the protected component
  return children
}

/**
 * App Component
 *
 * Main application component that sets up routing.
 *
 * ROUTING STRUCTURE:
 * - / → HomePage (public, shows login button)
 * - /dashboard → Dashboard (protected, requires authentication)
 */
function App() {
  return (
    <Routes>
      {/* Public route - anyone can access */}
      <Route path="/" element={<HomePage />} />

      {/* Protected route - requires authentication */}
      {/* ProtectedRoute will redirect to / if user is not logged in */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
