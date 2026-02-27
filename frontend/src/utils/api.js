/**
 * API Utility Module
 *
 * Centralized axios instance for making API requests to the backend.
 *
 * KEY SECURITY FEATURE:
 * - withCredentials: true ensures httpOnly cookies are automatically sent with every request
 * - This allows the JWT token to be sent securely without storing it in localStorage
 * - The browser handles cookie management automatically
 *
 * DEVELOPMENT vs PRODUCTION:
 * - In dev, Vite proxy forwards /api requests to http://localhost:5000
 * - In production, baseURL should be the full backend URL (e.g., https://yourapp.onrender.com)
 * - The proxy is configured in vite.config.js
 */

import axios from 'axios'

// Create axios instance with base configuration
// baseURL: '/api' means all requests will be prefixed with /api
// Example: api.get('/auth/user') becomes a request to /api/auth/user
const api = axios.create({
  baseURL: '/api',

  // CRITICAL: withCredentials must be true for httpOnly cookies to work
  // Without this, the browser won't send the jwt_token cookie with requests
  // This is what makes our authentication work - the cookie is sent automatically
  withCredentials: true,

  // Set default headers for all requests
  headers: {
    'Content-Type': 'application/json'
  }
})

// Export the configured axios instance
// Use this throughout the app instead of the raw axios import
// Example usage:
//   import api from './utils/api'
//   const response = await api.get('/auth/user')
export default api
