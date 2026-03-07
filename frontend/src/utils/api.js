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
// baseURL uses environment variable for production, falls back to '/api' for development
// Development: No VITE_API_URL set → baseURL = '/api' (Vite proxy forwards to localhost:5000)
// Production: VITE_API_URL set (e.g., 'https://yourapp.onrender.com') → baseURL = 'https://yourapp.onrender.com/api'
// Note: We append '/api' to the production URL to match the backend route structure
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api',

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
