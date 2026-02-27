/**
 * Main Entry Point
 *
 * This is where React starts rendering the application.
 * We wrap everything in BrowserRouter to enable client-side routing.
 *
 * WHY BrowserRouter:
 * - Enables navigation between pages without full page reloads
 * - Uses HTML5 History API (URLs look like /dashboard instead of /#/dashboard)
 * - Must wrap the entire app to make routing work in all components
 *
 * StrictMode:
 * - React's development mode that checks for potential issues
 * - Only runs in development, doesn't affect production
 * - Helps catch bugs early by running some checks twice
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* BrowserRouter enables client-side routing throughout the app */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
