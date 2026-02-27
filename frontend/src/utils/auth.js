/**
 * Authentication Utility Module
 *
 * Helper functions for managing user authentication state in React.
 *
 * WHY WE NEED THIS:
 * - The JWT token is stored in an httpOnly cookie (can't access with JavaScript)
 * - We need a way to check if the user is logged in
 * - We do this by calling the protected /api/auth/user endpoint
 * - If the cookie is valid, we get user data back
 * - If the cookie is invalid/missing, we get a 401 error
 *
 * SECURITY:
 * - We never access the JWT directly (it's httpOnly)
 * - We rely on the backend to validate the cookie
 * - This prevents XSS attacks from stealing tokens
 */

import api from './api'

/**
 * Check if user is authenticated and get their profile data.
 *
 * HOW IT WORKS:
 * 1. Makes a request to /api/auth/user (protected endpoint)
 * 2. The browser automatically sends the jwt_token cookie
 * 3. Backend validates the JWT and returns user data
 * 4. If successful, we return the user object
 * 5. If it fails (401), we return null (user not logged in)
 *
 * USE CASES:
 * - Call this when the app first loads to check authentication state
 * - Call this in ProtectedRoute to verify access before showing dashboard
 * - Store the result in React state to avoid repeated API calls
 *
 * @returns {Promise<Object|null>} User object if logged in, null if not
 */
export async function checkAuth() {
  try {
    // Call the protected endpoint
    // The jwt_token cookie is sent automatically (thanks to withCredentials: true)
    const response = await api.get('/auth/user')

    // If successful, response.data looks like:
    // {
    //   "success": true,
    //   "user": { "id": "...", "email": "...", "name": "...", "picture": "..." }
    // }
    return response.data.user
  } catch (error) {
    // If we get a 401 (unauthorized), the user is not logged in
    // If we get a network error, also treat as not logged in
    // Either way, return null to indicate no authentication
    return null
  }
}

/**
 * Log out the current user.
 *
 * HOW IT WORKS:
 * 1. Calls the protected /api/auth/logout endpoint
 * 2. Backend clears the jwt_token cookie
 * 3. Redirects user to homepage
 *
 * NOTES:
 * - Even if the API call fails, we redirect to homepage
 * - This ensures the user sees the login screen
 * - The cookie will be invalid/missing, so they can't access protected routes
 *
 * @returns {Promise<void>}
 */
export async function logout() {
  try {
    // Call the logout endpoint
    // Backend will clear the jwt_token cookie
    await api.post('/auth/logout')
  } catch (error) {
    // If logout fails, still redirect to homepage
    // The user won't be able to access protected routes anyway
    console.error('Logout failed:', error)
  } finally {
    // Always redirect to homepage after logout attempt
    // window.location.href causes a full page reload (clears React state)
    window.location.href = '/'
  }
}
