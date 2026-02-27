/**
 * HomePage Component
 *
 * Landing page for unauthenticated users.
 * Modern SaaS-style landing page with header, hero section, and features.
 *
 * LAYOUT:
 * - Header: App name (left) + Login button (right)
 * - Hero: Centered headline and slogan with lots of whitespace
 * - Features: 3 feature cards in a row showcasing key functionality
 *
 * DESIGN:
 * - White background throughout
 * - Clean, minimal, modern SaaS aesthetic
 * - Responsive layout that stacks on mobile
 */

import './HomePage.css'

function HomePage() {
  return (
    <div className="homepage">
      {/* ==================== Header ==================== */}
      {/* Fixed header with branding and login button */}
      <header className="homepage-header">
        {/* Left side: App name / logo with tagline */}
        <div className="header-left">
          <h1 className="homepage-logo">JustScheduleIt</h1>
          <span className="header-tagline">AI-powered calendar assistant</span>
        </div>

        {/* Login button - navigates to backend OAuth flow */}
        {/* Using <a> tag instead of button to ensure full page navigation */}
        <a href="/api/auth/login" className="header-login-btn">
          {/* Google "G" logo SVG */}
          <svg className="google-icon" viewBox="0 0 24 24" width="18" height="18">
            <g transform="matrix(1, 0, 0, 1, 27.009001, -39.238998)">
              <path fill="#4285F4" d="M -3.264 51.509 C -3.264 50.719 -3.334 49.969 -3.454 49.239 L -14.754 49.239 L -14.754 53.749 L -8.284 53.749 C -8.574 55.229 -9.424 56.479 -10.684 57.329 L -10.684 60.329 L -6.824 60.329 C -4.564 58.239 -3.264 55.159 -3.264 51.509 Z"/>
              <path fill="#34A853" d="M -14.754 63.239 C -11.514 63.239 -8.804 62.159 -6.824 60.329 L -10.684 57.329 C -11.764 58.049 -13.134 58.489 -14.754 58.489 C -17.884 58.489 -20.534 56.379 -21.484 53.529 L -25.464 53.529 L -25.464 56.619 C -23.494 60.539 -19.444 63.239 -14.754 63.239 Z"/>
              <path fill="#FBBC05" d="M -21.484 53.529 C -21.734 52.809 -21.864 52.039 -21.864 51.239 C -21.864 50.439 -21.724 49.669 -21.484 48.949 L -21.484 45.859 L -25.464 45.859 C -26.284 47.479 -26.754 49.299 -26.754 51.239 C -26.754 53.179 -26.284 54.999 -25.464 56.619 L -21.484 53.529 Z"/>
              <path fill="#EA4335" d="M -14.754 43.989 C -12.984 43.989 -11.404 44.599 -10.154 45.789 L -6.734 42.369 C -8.804 40.429 -11.514 39.239 -14.754 39.239 C -19.444 39.239 -23.494 41.939 -25.464 45.859 L -21.484 48.949 C -20.534 46.099 -17.884 43.989 -14.754 43.989 Z"/>
            </g>
          </svg>
          Login with Google
        </a>
      </header>

      {/* ==================== Hero Section ==================== */}
      {/* Centered headline and slogan with generous whitespace */}
      <section className="hero-section">
        <div className="hero-content">
          {/* Main headline - value proposition */}
          <h2 className="hero-headline">
            Manage your calendar with natural language
          </h2>

          {/* Slogan - catchy tagline */}
          <p className="hero-slogan">
            Your calendar, just say the word
          </p>

          {/* Get Started button - navigates to backend OAuth flow */}
          <a href="/api/auth/login" className="hero-cta-btn">
            Get Started
          </a>
        </div>
      </section>

      {/* ==================== Features Section ==================== */}
      {/* Three feature cards showcasing key functionality */}
      <section className="features-section">
        <div className="features-container">
          {/* Feature Card 1: Schedule */}
          <div className="feature-card">
            {/* Icon - Calendar with plus */}
            <div className="feature-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
                <line x1="12" y1="14" x2="12" y2="18"/>
                <line x1="10" y1="16" x2="14" y2="16"/>
              </svg>
            </div>

            {/* Title */}
            <h3 className="feature-title">Schedule Instantly</h3>

            {/* Description */}
            <p className="feature-description">
              Just type what you want and it appears on your calendar
            </p>
          </div>

          {/* Feature Card 2: Move & Cancel */}
          <div className="feature-card">
            {/* Icon - Edit/Move */}
            <div className="feature-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </div>

            {/* Title */}
            <h3 className="feature-title">Move & Cancel Easily</h3>

            {/* Description */}
            <p className="feature-description">
              Reschedule or remove events with a single sentence
            </p>
          </div>

          {/* Feature Card 3: View Calendar */}
          <div className="feature-card">
            {/* Icon - Eye/View */}
            <div className="feature-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </div>

            {/* Title */}
            <h3 className="feature-title">See Your Day Clearly</h3>

            {/* Description */}
            <p className="feature-description">
              View all your upcoming events at a glance
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default HomePage
