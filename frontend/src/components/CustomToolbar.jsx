/**
 * CustomToolbar Component
 *
 * Custom toolbar for react-big-calendar that replaces the default toolbar.
 *
 * LAYOUT:
 * - Left: Today button
 * - Center: Back button, Date label, Next button
 * - Right: Month, Week, Day, Agenda view buttons
 *
 * PROPS (from react-big-calendar):
 * - date: Current date being viewed
 * - view: Current view (month/week/day/agenda)
 * - label: Formatted date range label
 * - onNavigate: Function to navigate (TODAY, PREV, NEXT)
 * - onView: Function to change view
 */

import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth } from 'date-fns'
import './CustomToolbar.css'

function CustomToolbar({ date, view, label, onNavigate, onView }) {
  /**
   * Format the date label with year based on current view
   * @returns {string} Formatted date range label
   */
  const getDateLabel = () => {
    const currentDate = new Date(date)

    switch (view) {
      case 'month':
        // Show "Month Year" (e.g., "February 2026")
        return format(currentDate, 'MMMM yyyy')

      case 'week':
        // Show "Month Day-Day, Year" (e.g., "February 22-28, 2026")
        const weekStart = startOfWeek(currentDate)
        const weekEnd = endOfWeek(currentDate)
        const startMonth = format(weekStart, 'MMMM')
        const endMonth = format(weekEnd, 'MMMM')
        const year = format(weekEnd, 'yyyy')

        // If week spans two months
        if (startMonth !== endMonth) {
          return `${format(weekStart, 'MMM d')} – ${format(weekEnd, 'MMM d, yyyy')}`
        }
        // Same month
        return `${startMonth} ${format(weekStart, 'd')}–${format(weekEnd, 'd, yyyy')}`

      case 'day':
        // Show "Day, Month Date, Year" (e.g., "Friday, February 27, 2026")
        return format(currentDate, 'EEEE, MMMM d, yyyy')

      case 'agenda':
        // Show month range with year
        return format(currentDate, 'MMMM yyyy')

      default:
        // Fallback to default label with year added
        return `${label}, ${format(currentDate, 'yyyy')}`
    }
  }
  /**
   * Navigate to today's date
   */
  const goToToday = () => {
    onNavigate('TODAY')
  }

  /**
   * Navigate to previous period (week/month/day)
   */
  const goToPrev = () => {
    onNavigate('PREV')
  }

  /**
   * Navigate to next period (week/month/day)
   */
  const goToNext = () => {
    onNavigate('NEXT')
  }

  /**
   * Change calendar view
   * @param {string} newView - 'month', 'week', 'day', or 'agenda'
   */
  const changeView = (newView) => {
    onView(newView)
  }

  return (
    <div className="custom-toolbar">
      {/* Row 1: Navigation */}
      <div className="toolbar-row toolbar-row-nav">
        {/* Left: Today button */}
        <div className="toolbar-left">
          <button
            className="toolbar-btn"
            onClick={goToToday}
            type="button"
          >
            Today
          </button>
        </div>

        {/* Center: Back, Date, Next */}
        <div className="toolbar-center">
          <button
            className="toolbar-btn toolbar-btn-nav"
            onClick={goToPrev}
            type="button"
          >
            ← Back
          </button>

          <span className="toolbar-label">
            {getDateLabel()}
          </span>

          <button
            className="toolbar-btn toolbar-btn-nav"
            onClick={goToNext}
            type="button"
          >
            Next →
          </button>
        </div>

        {/* Right: Empty */}
        <div className="toolbar-right">
          {/* Empty space for symmetry */}
        </div>
      </div>

      {/* Row 2: View selector */}
      <div className="toolbar-row toolbar-row-views">
        <div className="toolbar-views">
          <button
            className={`toolbar-btn ${view === 'month' ? 'toolbar-btn-active' : ''}`}
            onClick={() => changeView('month')}
            type="button"
          >
            Month
          </button>
          <button
            className={`toolbar-btn ${view === 'week' ? 'toolbar-btn-active' : ''}`}
            onClick={() => changeView('week')}
            type="button"
          >
            Week
          </button>
          <button
            className={`toolbar-btn ${view === 'day' ? 'toolbar-btn-active' : ''}`}
            onClick={() => changeView('day')}
            type="button"
          >
            Day
          </button>
          <button
            className={`toolbar-btn ${view === 'agenda' ? 'toolbar-btn-active' : ''}`}
            onClick={() => changeView('agenda')}
            type="button"
          >
            Agenda
          </button>
        </div>
      </div>
    </div>
  )
}

export default CustomToolbar
